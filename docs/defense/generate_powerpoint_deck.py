#!/usr/bin/env python3
"""Generate the ILB defense PowerPoint deck without third-party dependencies.

The deck content mirrors docs/defense/slides.md and the release evidence docs.
It writes a standards-compliant .pptx Open XML package that can be opened in
PowerPoint, LibreOffice, or Keynote.
"""
from __future__ import annotations

# ruff: noqa: E501
from datetime import UTC, datetime
from pathlib import Path
from textwrap import dedent
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

OUT = Path(__file__).with_name("ilb-incubator-defense-deck.pptx")

# 16:9 widescreen dimensions in English Metric Units.
SLIDE_W = 13_333_500
SLIDE_H = 7_500_000

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}

SLIDES = [
    {
        "title": "ILB Incubator Management Platform",
        "subtitle": "Defense deck — local-first microservices platform",
        "bullets": [
            "Staff portal for internal incubator operations.",
            "Client portal for incubated companies.",
            "Public booking request flow for unauthenticated users.",
            "Ten Django/DRF services behind one Nginx gateway plus a Next.js 14 + Ant Design frontend.",
        ],
        "footer": "Sources: README.md; docs/defense/slides.md",
    },
    {
        "title": "Phase 2 scope delivered",
        "subtitle": "Planned service wave is represented in code and defense docs",
        "bullets": [
            "Auth/User, Company, Document, Contract, Finance, Space, Booking, Inventory, Ticket, and Dashboard.",
            "Each service has its own Django app/runtime boundary and database.",
            "Inventory and Dashboard are included in the defense path, not deferred.",
            "Frontend placeholder pages were replaced with staff/client/public operational surfaces.",
        ],
        "footer": "Sources: docs/implementation-audit-report.md; docs/architecture.md",
    },
    {
        "title": "Architecture boundaries",
        "subtitle": "Strict microservices in a monorepo",
        "bullets": [
            "One PostgreSQL database per bounded context; no shared ORM models or schemas.",
            "Nginx routes /api/<service>/... to internal-only service ports.",
            "Gateway auth_request validates JWTs against auth-service.",
            "Trusted identity headers: X-User-Id, X-User-Role, X-Company-Id.",
            "MinIO stores document objects; document-service owns metadata.",
        ],
        "footer": "Sources: docs/architecture.md; gateway/nginx.conf",
    },
    {
        "title": "Deployment topology",
        "subtitle": "Repeatable local stack for assessment and demo",
        "bullets": [
            "Frontend is served through the gateway; APIs stay under /api/... .",
            "Backend services are private to the Docker network.",
            "PostgreSQL, Redis, RabbitMQ, and MinIO provide local infrastructure.",
            "Scheduled work uses management-command sidecars and host-style cron, not Celery.",
            "Demo entry points: make demo, make up, Tilt live-reload path.",
        ],
        "footer": "Sources: README.md; docs/deploy.md; infra/cron/",
    },
    {
        "title": "Event-driven workflows",
        "subtitle": "RabbitMQ topic exchange: incubator.events",
        "bullets": [
            "Standard event envelope: event_id, event_type, occurred_at, payload.",
            "contract.activated updates finance payment projections and space contract projections.",
            "booking.approved/cancelled/completed update space, inventory, finance, and dashboard projections.",
            "payment.recorded refreshes financial aggregates.",
            "Consumers dedupe by event_id for safe retries and replays.",
        ],
        "footer": "Sources: docs/events.md; docs/architecture.md",
    },
    {
        "title": "Role-based product surfaces",
        "subtitle": "Staff, client, and public flows are intentionally separated",
        "bullets": [
            "Staff: dashboard KPIs, companies, contracts, finance, spaces, bookings, inventory, tickets, users.",
            "Client: company profile, contract, payments, bookings, support tickets, documents.",
            "Public: booking request form without authentication.",
            "Client views are scoped by X-Company-Id rather than trusting browser-provided company ids.",
        ],
        "footer": "Sources: docs/user.md; frontend/app/",
    },
    {
        "title": "Recommended live demo flow",
        "subtitle": "Business story before implementation details",
        "bullets": [
            "Start stack and seed representative data; login as Director/Staff.",
            "Review dashboard health and operational KPIs.",
            "Inspect company status, active contracts, finance totals, and payment states.",
            "Show spaces/bookings/inventory lifecycle effects and ticket separation.",
            "Login as Client to verify company-scoped data; finish with public booking request.",
        ],
        "footer": "Sources: docs/defense/demo-script.md; docs/defense/checklist.md",
    },
    {
        "title": "Functional coverage map",
        "subtitle": "Rubric-critical domains and evidence to show",
        "bullets": [
            "Auth/User: login, role routing, Director-only user management.",
            "Company/Contract: company lifecycle, maturity/status, active contract data.",
            "Finance/Space/Booking: summaries, occupancy, public/client/staff flows.",
            "Inventory/Ticket/Document: assignments, staff/client support, upload/list/download integration points.",
            "Dashboard: cross-service operational aggregates and drill-through links.",
        ],
        "footer": "Sources: docs/defense/release-evidence.md",
    },
    {
        "title": "Quality and verification evidence",
        "subtitle": "Local host-only gate and browser smoke are current evidence",
        "bullets": [
            "make local-gate-host PASS on 2026-05-25: lint, format, frontend typecheck/unit/build, infra, libs, services.",
            "Frontend mocked Playwright suite PASS: 11 tests for login, portal scoping, dashboard, inventory, booking, and users.",
            "Backend service tests include migration dry-runs and pytest per service.",
            "Known environment blocker: Docker socket access can prevent make demo and live gateway e2e on restricted hosts.",
        ],
        "footer": "Sources: docs/defense/local-qa-evidence.md; docs/defense/release-evidence.md",
    },
    {
        "title": "Risks, roadmap, and close",
        "subtitle": "Transparent handoff for defense readiness",
        "bullets": [
            "Immediate: rerun make demo and gateway Playwright smoke on a Docker-enabled workstation.",
            "Immediate: export PDF/record backup demo using the documented storyboard.",
            "Future: richer dashboard charts, deeper domain detail forms, stronger observability, CI artifact capture.",
            "Conclusion: Phase 2 is integration-ready locally with documented demo flow, evidence, and known host-only blocker.",
        ],
        "footer": "Sources: docs/defense/checklist.md; docs/defense/demo-script.md",
    },
]


def xml_text(text: str) -> str:
    return escape(text, {"\n": "&#10;"})


def shape_text(spid: int, name: str, x: int, y: int, cx: int, cy: int, paragraphs: list[str], font_size: int = 2400,
               color: str = "1F2937", bold_first: bool = False, bullet: bool = False) -> str:
    p_xml = []
    for idx, para in enumerate(paragraphs):
        bullet_xml = '<a:buChar char="•"/>' if bullet else '<a:buNone/>'
        indent = ' marL="342900" indent="-228600"' if bullet else ""
        bold = ' b="1"' if bold_first and idx == 0 else ""
        p_xml.append(f'''
          <a:p>
            <a:pPr{indent}>{bullet_xml}</a:pPr>
            <a:r><a:rPr lang="en-US" sz="{font_size}"{bold}><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:rPr><a:t>{xml_text(para)}</a:t></a:r>
            <a:endParaRPr lang="en-US" sz="{font_size}"/>
          </a:p>''')
    return f'''
      <p:sp>
        <p:nvSpPr><p:cNvPr id="{spid}" name="{xml_text(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
        <p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{''.join(p_xml)}</p:txBody>
      </p:sp>'''


def rect(spid: int, name: str, x: int, y: int, cx: int, cy: int, fill: str, line: str | None = None) -> str:
    line_xml = f'<a:ln><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>' if line else '<a:ln><a:noFill/></a:ln>'
    return f'''
      <p:sp>
        <p:nvSpPr><p:cNvPr id="{spid}" name="{xml_text(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>{line_xml}</p:spPr>
      </p:sp>'''


def slide_xml(slide: dict[str, object], n: int) -> str:
    title = str(slide["title"])
    subtitle = str(slide["subtitle"])
    bullets = list(slide["bullets"])
    footer = str(slide["footer"])
    shapes = [
        rect(2, "Header band", 0, 0, SLIDE_W, 820_000, "0F3D3E"),
        rect(3, "Accent bar", 0, 820_000, SLIDE_W, 70_000, "22C55E"),
        shape_text(4, "Title", 520_000, 130_000, 12_200_000, 350_000, [title], font_size=3000, color="FFFFFF", bold_first=True),
        shape_text(5, "Subtitle", 540_000, 500_000, 11_800_000, 230_000, [subtitle], font_size=1450, color="D1FAE5"),
        shape_text(6, "Bullets", 780_000, 1_230_000, 11_900_000, 5_250_000, [str(b) for b in bullets], font_size=2050, color="1F2937", bullet=True),
        rect(7, "Footer divider", 520_000, 6_780_000, 12_050_000, 18_000, "CBD5E1"),
        shape_text(8, "Footer", 540_000, 6_880_000, 10_700_000, 250_000, [footer], font_size=950, color="64748B"),
        shape_text(9, "Slide number", 12_220_000, 6_880_000, 600_000, 250_000, [f"{n}/{len(SLIDES)}"], font_size=950, color="64748B"),
    ]
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="{NS['a']}" xmlns:r="{NS['r']}" xmlns:p="{NS['p']}">
  <p:cSld><p:spTree>
    <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
    <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    {''.join(shapes)}
  </p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>'''


def content_types() -> str:
    overrides = "\n".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        for i in range(1, len(SLIDES) + 1)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  {overrides}
</Types>'''


def rels_root() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''


def presentation_xml() -> str:
    slide_ids = "\n".join(f'<p:sldId id="{255+i}" r:id="rId{i}"/>' for i in range(1, len(SLIDES) + 1))
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="{NS['a']}" xmlns:r="{NS['r']}" xmlns:p="{NS['p']}" saveSubsetFonts="1">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{len(SLIDES)+1}"/></p:sldMasterIdLst>
  <p:sldIdLst>{slide_ids}</p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>'''


def presentation_rels() -> str:
    rels = []
    for i in range(1, len(SLIDES) + 1):
        rels.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>')
    rels.append(f'<Relationship Id="rId{len(SLIDES)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>')
    rels.append(f'<Relationship Id="rId{len(SLIDES)+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>')
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(rels)}</Relationships>'''


def slide_rels() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>'''


def slide_layout_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="{NS['a']}" xmlns:r="{NS['r']}" xmlns:p="{NS['p']}" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>'''


def slide_layout_rels() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>'''


def slide_master_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="{NS['a']}" xmlns:r="{NS['r']}" xmlns:p="{NS['p']}" preserve="1">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>'''


def slide_master_rels() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>'''


def theme_xml() -> str:
    return dedent('''\
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="ILB Defense">
      <a:themeElements>
        <a:clrScheme name="ILB"><a:dk1><a:srgbClr val="111827"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="0F3D3E"/></a:dk2><a:lt2><a:srgbClr val="F8FAFC"/></a:lt2><a:accent1><a:srgbClr val="0F3D3E"/></a:accent1><a:accent2><a:srgbClr val="22C55E"/></a:accent2><a:accent3><a:srgbClr val="2563EB"/></a:accent3><a:accent4><a:srgbClr val="F59E0B"/></a:accent4><a:accent5><a:srgbClr val="7C3AED"/></a:accent5><a:accent6><a:srgbClr val="DC2626"/></a:accent6><a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink></a:clrScheme>
        <a:fontScheme name="Aptos"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme>
        <a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
      </a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/>
    </a:theme>
    ''')


def core_xml() -> str:
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>ILB Incubator Management Platform — Defense Deck</dc:title>
  <dc:subject>SDL project defense deck</dc:subject>
  <dc:creator>SDL Project Group 20</dc:creator>
  <cp:keywords>ILB, incubator, microservices, Django, Next.js, defense</cp:keywords>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''


def app_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Python stdlib Open XML generator</Application><PresentationFormat>Widescreen</PresentationFormat><Slides>{len(SLIDES)}</Slides><Company>SDL Project Group 20</Company>
</Properties>'''


def build() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUT, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types())
        z.writestr("_rels/.rels", rels_root())
        z.writestr("docProps/core.xml", core_xml())
        z.writestr("docProps/app.xml", app_xml())
        z.writestr("ppt/presentation.xml", presentation_xml())
        z.writestr("ppt/_rels/presentation.xml.rels", presentation_rels())
        z.writestr("ppt/slideMasters/slideMaster1.xml", slide_master_xml())
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", slide_master_rels())
        z.writestr("ppt/slideLayouts/slideLayout1.xml", slide_layout_xml())
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", slide_layout_rels())
        z.writestr("ppt/theme/theme1.xml", theme_xml())
        for i, slide in enumerate(SLIDES, start=1):
            z.writestr(f"ppt/slides/slide{i}.xml", slide_xml(slide, i))
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", slide_rels())
    print(f"Wrote {OUT} ({len(SLIDES)} slides)")


if __name__ == "__main__":
    build()
