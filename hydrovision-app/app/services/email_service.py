"""
email_service.py — Servicio de emails transaccionales y lifecycle
HydroVision AG

Responsabilidades:
  - Renderizar templates Jinja2 de email
  - Enviar via SMTP (async-safe con run_in_executor)
  - Generar datos agregados para informes desde telemetry/irrigation_log

Uso:
  from app.services.email_service import EmailService
  svc = EmailService(templates)
  await svc.send_annual_report(client, campaign_year)
  await svc.send_lifecycle(client, "campaign_start")
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from asyncio import get_event_loop
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from jinja2 import Environment
from sqlalchemy import func, and_

from app import config
from app.models import SessionLocal, Telemetry, IrrigationLog
from app.services.phenology import get_crop_group, get_phase, get_next_phase

log = logging.getLogger("hydrovision.email")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ZoneInfo:
    """Datos de una zona para generar emails por zona."""
    zone_id: int
    zone_name: str
    varietal: str              # "vid - malbec", "olivo", etc.
    node_ids: list[str] = field(default_factory=list)


@dataclass
class ClientInfo:
    """Datos minimos de un cliente para generar emails."""
    name: str
    email: str
    crop: str                  # cultivo predominante (fallback)
    total_ha: float
    tier: int
    region: str
    node_ids: list[str] = field(default_factory=list)
    zones: list[ZoneInfo] = field(default_factory=list)
    install_date: datetime | None = None
    agronomist_email: str | None = None


@dataclass
class CampaignStats:
    """Metricas agregadas de una campana para un cliente."""
    stress_events: int = 0
    water_saved_m3: float = 0.0
    water_saved_pct: float = 0.0
    roi_usd: float = 0.0
    roi_multiple: float = 0.0
    subscription_cost: float = 0.0
    total_measurements: int = 0
    auto_irrigations: int = 0
    r2_start: float | None = None
    r2_end: float | None = None
    frost_events: int = 0
    chill_hours: float = 0.0
    events: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class EmailService:

    def __init__(self, jinja_env: Environment):
        self.jinja = jinja_env

    # -- Aggregation --------------------------------------------------------

    def get_campaign_stats(
        self,
        node_ids: list[str],
        start: datetime,
        end: datetime,
        tier: int,
        total_ha: float,
        crop: str,
    ) -> CampaignStats:
        """Genera estadisticas de campana desde la base de datos."""
        db = SessionLocal()
        try:
            ts_start = int(start.timestamp())
            ts_end = int(end.timestamp())

            # Total de mediciones
            total_measurements = (
                db.query(func.count(Telemetry.id))
                .filter(
                    Telemetry.node_id.in_(node_ids),
                    Telemetry.ts >= ts_start,
                    Telemetry.ts <= ts_end,
                )
                .scalar()
            ) or 0

            # Eventos de estres (CWSI >= 0.6)
            stress_events = (
                db.query(func.count(Telemetry.id))
                .filter(
                    Telemetry.node_id.in_(node_ids),
                    Telemetry.ts >= ts_start,
                    Telemetry.ts <= ts_end,
                    Telemetry.cwsi >= 0.6,
                )
                .scalar()
            ) or 0

            # Lluvia total (proxy para ahorro — simplificado)
            total_rain = (
                db.query(func.sum(Telemetry.rain_mm))
                .filter(
                    Telemetry.node_id.in_(node_ids),
                    Telemetry.ts >= ts_start,
                    Telemetry.ts <= ts_end,
                )
                .scalar()
            ) or 0.0

            # Riegos automaticos
            auto_irrigations = 0
            try:
                auto_irrigations = (
                    db.query(func.count(IrrigationLog.id))
                    .filter(
                        IrrigationLog.node_id.in_(node_ids),
                        IrrigationLog.created_at >= start,
                        IrrigationLog.created_at <= end,
                    )
                    .scalar()
                ) or 0
            except Exception:
                pass

            # Heladas (T_air < 0)
            frost_events = (
                db.query(func.count(Telemetry.id))
                .filter(
                    Telemetry.node_id.in_(node_ids),
                    Telemetry.ts >= ts_start,
                    Telemetry.ts <= ts_end,
                    Telemetry.t_air < 0,
                )
                .scalar()
            ) or 0

            # Calculos derivados
            price_per_ha = {1: 95, 2: 150, 3: 250}
            subscription_cost = total_ha * price_per_ha.get(tier, 150)

            # Estimacion ROI conservadora (12% rendimiento recuperado)
            crop_income = {
                "vid": 9600, "malbec": 9600, "sauvignon": 9600,
                "olivo": 5500, "citrus": 8500, "limon": 8500,
                "cereza": 30000, "pistacho": 18000, "nogal": 10000,
            }
            income = crop_income.get(crop.lower().split()[0], 8000)
            roi_usd = round(total_ha * income * 0.12, 0) if stress_events > 0 else 0
            roi_multiple = round(roi_usd / subscription_cost, 1) if subscription_cost > 0 else 0

            # Ahorro de agua estimado (15% vs calendario)
            water_per_ha_m3 = 5000  # m3/ha/campana tipico riego tecnificado
            water_saved_m3 = round(total_ha * water_per_ha_m3 * 0.15)
            water_saved_pct = 15.0

            return CampaignStats(
                stress_events=stress_events,
                water_saved_m3=water_saved_m3,
                water_saved_pct=water_saved_pct,
                roi_usd=roi_usd,
                roi_multiple=roi_multiple,
                subscription_cost=subscription_cost,
                total_measurements=total_measurements,
                auto_irrigations=auto_irrigations,
                frost_events=frost_events,
                recommendations=self._generate_recommendations(
                    stress_events, auto_irrigations, tier, total_measurements
                ),
            )
        finally:
            db.close()

    def _generate_recommendations(
        self, stress: int, irrigations: int, tier: int, measurements: int
    ) -> list[str]:
        recs = []
        if stress > 10 and tier == 1:
            recs.append(
                "Tu campo tuvo muchos eventos de estres. Con Tier 2, "
                "el riego se activa automaticamente antes del dano — consultanos sobre el upgrade."
            )
        if measurements > 500_000:
            recs.append(
                "Tu modelo tiene suficiente historial para activar prediccion avanzada. "
                "Contacta soporte para habilitarla."
            )
        if stress == 0:
            recs.append(
                "Excelente campana sin estres critico. Revisa que los umbrales de alerta "
                "no esten demasiado altos — asegurate de que el sistema alerte a tiempo."
            )
        return recs

    # -- Zone helpers -------------------------------------------------------

    @staticmethod
    def _build_zone_context(zones: list[ZoneInfo], month: int) -> list[dict]:
        """Construye contexto de zonas con fenología para los templates."""
        result = []
        for z in zones:
            group = get_crop_group(z.varietal)
            phase = get_phase(group, month)
            next_ph = get_next_phase(group, month)
            varietal_short = z.varietal.split(" - ")[-1].strip().capitalize() if " - " in z.varietal else z.varietal.capitalize()
            result.append({
                "zone_id": z.zone_id,
                "zone_name": z.zone_name,
                "varietal": z.varietal,
                "varietal_short": varietal_short,
                "crop_group": group,
                "node_ids": z.node_ids,
                "nodos": len(z.node_ids),
                "phase_display": phase.display,
                "phase_description": phase.description,
                "phase_risk": phase.risk,
                "phase_stress_note": phase.stress_note,
                "next_phase_display": next_ph.display if next_ph else None,
            })
        return result

    # -- Rendering ----------------------------------------------------------

    def render_annual_report(self, client: ClientInfo, stats: CampaignStats, campaign_year: int) -> str:
        tpl = self.jinja.get_template("emails/annual_report.html")
        years_active = 1
        if client.install_date:
            years_active = max(1, (datetime.now() - client.install_date).days // 365)

        group = get_crop_group(client.crop)
        crop_short = client.crop.split(" - ")[-1].strip().capitalize() if " - " in client.crop else client.crop.capitalize()
        zones_ctx = self._build_zone_context(client.zones, datetime.now().month)

        return tpl.render(
            subject=f"Informe anual — Campaña {campaign_year}",
            client_name=client.name,
            crop=client.crop,
            crop_short=crop_short,
            crop_group=group,
            total_ha=client.total_ha,
            tier=client.tier,
            region=client.region,
            years_active=years_active,
            campaign_year=campaign_year,
            zones=zones_ctx,
            stress_events=stats.stress_events,
            water_saved_m3=stats.water_saved_m3,
            water_saved_pct=stats.water_saved_pct,
            roi_usd=f"{stats.roi_usd:,.0f}",
            roi_multiple=f"{stats.roi_multiple:.1f}",
            subscription_cost=f"{stats.subscription_cost:,.0f}",
            total_measurements=f"{stats.total_measurements:,}",
            r2_start=stats.r2_start,
            r2_end=stats.r2_end,
            events=stats.events,
            recommendations=stats.recommendations,
            frost_events=stats.frost_events,
        )

    def render_lifecycle(self, client: ClientInfo, email_type: str, **kwargs) -> tuple[str, str]:
        """Renderiza un email lifecycle. Retorna (subject, html_body)."""
        tpl = self.jinja.get_template("emails/lifecycle.html")

        # Fenología (cultivo predominante para subject)
        group = get_crop_group(client.crop)
        month = kwargs.get("month") or datetime.now().month
        phase = get_phase(group, month)
        next_phase = get_next_phase(group, month)

        crop_short = client.crop.split(" - ")[-1].strip().capitalize() if " - " in client.crop else client.crop.capitalize()
        zones_ctx = self._build_zone_context(client.zones, month)

        # Subject: si hay múltiples variedades, usar genérico
        n_groups = len({z["crop_group"] for z in zones_ctx}) if zones_ctx else 1
        label = f"{len(zones_ctx)} zonas" if n_groups > 1 else crop_short

        titles = {
            "campaign_start": f"{label}: tu sistema arrancó la campaña",
            "first_report": f"{label}: {kwargs.get('stress_events', 0)} eventos detectados",
            "peak_heat": f"{label}: tu sistema actuó {kwargs.get('actions_this_week', 0)} veces esta semana",
            "campaign_end": f"{label}: resumen de campaña — {kwargs.get('stress_events', 0)} alertas",
            "offseason": f"{label}: {kwargs.get('frost_events', 0)} heladas monitoreadas",
            "pre_campaign": f"{label}: tu modelo tiene {kwargs.get('total_data_days', 0)} días de datos",
        }
        title = titles.get(email_type, "Novedades de HydroVision")

        html = tpl.render(
            subject=title,
            title=title,
            email_type=email_type,
            client_name=client.name,
            crop=client.crop,
            crop_short=crop_short,
            crop_group=group,
            total_ha=client.total_ha,
            tier=client.tier,
            region=client.region,
            zones=zones_ctx,
            phase_name=phase.name,
            phase_display=phase.display,
            phase_description=phase.description,
            phase_risk=phase.risk,
            phase_stress_note=phase.stress_note,
            next_phase_display=next_phase.display if next_phase else None,
            **kwargs,
        )
        return title, html

    # -- Sending ------------------------------------------------------------

    def _send_smtp(self, to: str, subject: str, html_body: str, cc: str | None = None):
        """Envia email via SMTP. Bloqueante — llamar desde executor."""
        if not config.SMTP_HOST:
            log.warning("SMTP no configurado — email NO enviado a %s: %s", to, subject)
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = config.EMAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        recipients = [to]
        if cc:
            recipients.append(cc)

        try:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as server:
                server.starttls()
                if config.SMTP_USER:
                    server.login(config.SMTP_USER, config.SMTP_PASS)
                server.sendmail(config.EMAIL_FROM, recipients, msg.as_string())
            log.info("Email enviado a %s: %s", to, subject)
            return True
        except Exception as e:
            log.error("Error enviando email a %s: %s", to, e)
            return False

    async def send(self, to: str, subject: str, html_body: str, cc: str | None = None) -> bool:
        """Envia email async (usa thread pool para SMTP bloqueante)."""
        loop = get_event_loop()
        return await loop.run_in_executor(None, self._send_smtp, to, subject, html_body, cc)

    async def send_annual_report(self, client: ClientInfo, campaign_year: int) -> bool:
        """Genera y envia el informe anual a un cliente."""
        now = datetime.now()
        start = datetime(campaign_year, 10, 1)
        end = datetime(campaign_year + 1, 3, 31)
        if end > now:
            end = now

        stats = self.get_campaign_stats(
            node_ids=client.node_ids,
            start=start,
            end=end,
            tier=client.tier,
            total_ha=client.total_ha,
            crop=client.crop,
        )
        html = self.render_annual_report(client, stats, campaign_year)
        subject = f"Tu informe anual HydroVision — Campana {campaign_year}"
        return await self.send(
            to=client.email,
            subject=subject,
            html_body=html,
            cc=client.agronomist_email,
        )

    async def send_lifecycle_email(self, client: ClientInfo, email_type: str, **kwargs) -> bool:
        """Genera y envia un email lifecycle a un cliente."""
        subject, html = self.render_lifecycle(client, email_type, **kwargs)
        return await self.send(
            to=client.email,
            subject=subject,
            html_body=html,
            cc=client.agronomist_email,
        )
