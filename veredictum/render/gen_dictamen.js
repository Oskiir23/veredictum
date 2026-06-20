/* Veredictum — renderer del dictamen pericial de correo.
   Reutiliza el estilo de la plantilla maestra de Óscar (gen_informe_correo.js).
   Uso: node gen_dictamen.js <datos.json> <salida.docx>
   Los HECHOS (hashes, autenticación, IOCs, adjuntos) vienen del análisis real;
   la NARRATIVA (veredicto, conclusiones, incertidumbres) la aporta el agente.   */
const fs = require("fs");
const docx = require("docx"); // se resuelve vía NODE_PATH=C:\Users\seosc\node_modules
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, TabStopType,
  TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageNumber, PageBreak, SectionType
} = docx;

const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OUT = process.argv[3];
const N = D.narrativa || {};
const C = D.correo || {};
const AUTH = C.autenticacion || {};
const IOC = D.iocs || {};

/* ============================ PALETA ============================ */
const NAVY = "1F3864", TEAL = "2E8FAE", HEADERFILL = "1F3864", ALTFILL = "EAF1F8", GRIS = "7F7F7F";
const CW = 9360;

/* ============================ HELPERS ============================ */
const tlp = (size = 18) =>
  new TextRun({ text: " TLP:RED ", bold: true, color: "FF0000", size,
    shading: { type: ShadingType.CLEAR, fill: "000000", color: "auto" } });
const P = (children, opts = {}) =>
  new Paragraph({ spacing: { after: 120, line: 276 },
    children: (Array.isArray(children) ? children : [new TextRun({ text: children })]), ...opts });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (children) => new Paragraph({ numbering: { reference: "bul", level: 0 },
  spacing: { after: 60 }, children: Array.isArray(children) ? children : [new TextRun(children)] });
const spacer = () => new Paragraph({ spacing: { after: 60 }, children: [] });

const border = { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" };
const borders = { top: border, left: border, bottom: border, right: border };
const cellMargins = { top: 60, left: 110, bottom: 60, right: 110 };
function cell(content, { w, head = false, fill, align } = {}) {
  const runs = Array.isArray(content) ? content
    : [new TextRun({ text: String(content), bold: head, color: head ? "FFFFFF" : undefined })];
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: head ? HEADERFILL : (fill || "FFFFFF") },
    margins: cellMargins, verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ alignment: align, spacing: { after: 0 }, children: runs })] });
}
function table(headers, rows, colWidths) {
  const headRow = new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, { w: colWidths[i], head: true })) });
  const bodyRows = rows.map((r, ri) => new TableRow({ children: r.map((c, i) => cell(c, { w: colWidths[i], fill: ri % 2 ? ALTFILL : "FFFFFF" })) }));
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: colWidths, rows: [headRow, ...bodyRows] });
}
function kv(pairs, lw = 3000) {
  const rw = CW - lw;
  return new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: [lw, rw],
    rows: pairs.map((p, ri) => new TableRow({ children: [
      cell([new TextRun({ text: p[0], bold: true })], { w: lw, fill: "D9E2F3" }),
      cell(Array.isArray(p[1]) ? p[1] : [new TextRun({ text: String(p[1]) })], { w: rw, fill: ri % 2 ? "FFFFFF" : ALTFILL })
    ] })) });
}
let TBL = 0;
const tablecap = (t) => { TBL++; return new Paragraph({ spacing: { before: 180, after: 60 }, keepNext: true,
  children: [ new TextRun({ text: `Tabla ${TBL}. `, bold: true, color: NAVY, size: 18 }),
    new TextRun({ text: t, italics: true, color: "595959", size: 18 }) ] }); };

/* ============================ HEADER / FOOTER ============================ */
const headerTLP = new Header({ children: [ new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { after: 0 }, children: [tlp(18)] }) ] });
const footerStd = new Footer({ children: [ new Paragraph({
  tabStops: [{ type: TabStopType.RIGHT, position: CW }],
  border: { top: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF", space: 4 } }, spacing: { before: 40 },
  children: [
    new TextRun({ text: `Caso ${D.caso_id} — Documento clasificado TLP:RED · Confidencial, uso exclusivamente judicial`, size: 14, color: GRIS }),
    new TextRun({ text: "\t" }), tlp(14),
    new TextRun({ text: "   Pág. ", size: 14, color: GRIS }),
    new TextRun({ children: [PageNumber.CURRENT], size: 14, color: GRIS }),
    new TextRun({ text: "/", size: 14, color: GRIS }),
    new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 14, color: GRIS })
  ] }) ] });

/* ============================ PORTADA ============================ */
const portada = [
  new Paragraph({ alignment: AlignmentType.RIGHT, children: [tlp(22)] }),
  new Paragraph({ spacing: { before: 1200 }, children: [] }),
  new Paragraph({ spacing: { after: 60 }, children: [ new TextRun({ text: "INFORME PERICIAL", bold: true, color: NAVY, size: 64 }) ] }),
  new Paragraph({ spacing: { after: 40 }, children: [ new TextRun({ text: "DE ANÁLISIS FORENSE DE CORREO ELECTRÓNICO", bold: true, color: TEAL, size: 32 }) ] }),
  new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 18, color: TEAL, space: 6 } }, spacing: { after: 300 }, children: [] }),
  new Paragraph({ spacing: { after: 200 }, children: [
    new TextRun({ text: "BORRADOR — ", bold: true, color: "C00000", size: 24 }),
    new TextRun({ text: "documento generado automáticamente por Veredictum. Requiere revisión y validación de un perito antes de su emisión.", italics: true, color: "C00000", size: 20 }) ] }),
  new Paragraph({ spacing: { after: 80 }, children: [ new TextRun({ text: "Expediente Nº: ", bold: true, size: 26 }), new TextRun({ text: String(D.caso_id), size: 26 }) ] }),
  new Paragraph({ spacing: { after: 80 }, children: [ new TextRun({ text: "Evidencia: ", bold: true, size: 26 }), new TextRun({ text: String(C.evidencia || "—"), size: 26 }) ] }),
  new Paragraph({ spacing: { after: 80 }, children: [ new TextRun({ text: "Fecha de emisión: ", bold: true, size: 26 }), new TextRun({ text: String(D.fecha_emision || ""), size: 26 }) ] }),
  new Paragraph({ spacing: { after: 80 }, children: [ new TextRun({ text: "Perito informático forense: ", bold: true, size: 26 }), new TextRun({ text: "Óscar Carretero Hilillo", size: 26 }) ] }),
  new Paragraph({ spacing: { before: 2200 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.CENTER, border: { top: { style: BorderStyle.SINGLE, size: 4, color: GRIS, space: 6 } }, children: [
    new TextRun({ text: "Documento clasificado como ", size: 16, color: GRIS }), tlp(16),
    new TextRun({ text: ". Su contenido es estrictamente confidencial y no puede difundirse fuera de las personas concretas a las que se entrega de forma nominal.", size: 16, color: GRIS }) ] }),
];

const indice = [ H1("ÍNDICE"), new TableOfContents("Tabla de contenido", { hyperlink: true, headingStyleRange: "1-3" }), new Paragraph({ children: [new PageBreak()] }) ];

/* ============================ 1. PERITO ============================ */
const perito = [
  H1("1. IDENTIFICACIÓN DEL PERITO Y DECLARACIÓN"),
  tablecap("Datos identificativos del perito."),
  kv([
    ["Nombre y apellidos", "Óscar Carretero Hilillo"],
    ["DNI", "«00000000-X»"],
    ["Titulación", "Técnico Superior en ASIR · Máster en Ciberseguridad"],
    ["Acreditación profesional", "Perito Informático Forense"],
    ["Correo electrónico", "seoscarretero@gmail.com"],
  ], 3200),
  spacer(),
  H2("1.1. Juramento o promesa del perito"),
  P("El perito que suscribe JURA / PROMETE decir verdad y manifiesta que ha actuado con la mayor objetividad posible, tomando en consideración tanto lo que pueda favorecer como lo que sea susceptible de causar perjuicio a cualquiera de las partes, y que conoce las sanciones penales en las que podría incurrir si incumpliere su deber como perito (arts. 335.2 y 340 de la Ley 1/2000, de Enjuiciamiento Civil; art. 459 del Código Penal)."),
  P("Asimismo, declara no tener relación de parentesco, amistad íntima o enemistad manifiesta con ninguna de las partes, ni interés directo o indirecto en el objeto de la pericia, comprometiéndose a realizar el dictamen conforme a la buena ciencia y práctica forense (ISO/IEC 27037; NIST SP 800-86)."),
  spacer(),
  P([new TextRun({ text: "Fdo.: Óscar Carretero Hilillo", bold: true })]),
];

/* ============================ 2. OBJETO ============================ */
const objeto = [
  H1("2. OBJETO DEL INFORME"),
  P(`El presente informe pericial tiene por objeto el análisis forense del archivo de correo electrónico ${C.evidencia || "entregado"}, con la finalidad de identificar y justificar técnicamente los Indicadores de Compromiso (IoC) y anomalías presentes en su código fuente, así como de determinar la naturaleza y peligrosidad de los artefactos que contiene.`),
  P([new TextRun({ text: "Hipótesis de investigación: ", bold: true }), new TextRun({ text: `¿constituye el mensaje «${C.asunto || ""}» un correo malicioso (phishing y/o vector de código dañino) dirigido a la organización receptora?` })]),
];

/* ============================ 3. ALCANCE Y LIMITACIONES ============================ */
const alcance = [
  H1("3. ALCANCE Y LIMITACIONES"),
  H2("3.1. Alcance del trabajo"),
  P(`La actuación pericial se centró en el análisis estático del archivo ${C.evidencia || "de correo"} y de los artefactos derivados de él (cabeceras, autenticación, cuerpo, enlaces y adjuntos).`),
  P([new TextRun({ text: "Todo el procedimiento se ha realizado bajo el principio de mismidad", bold: true }), new TextRun({ text: ", garantizando que la copia de trabajo es idéntica al original mediante el cálculo de funciones resumen criptográficas (hash), preservándose inalterado el archivo original." })]),
  spacer(),
  H2("3.2. Limitaciones"),
  bullet([new TextRun({ text: "El análisis ha sido estrictamente estático. ", bold: true }), new TextRun({ text: "Por seguridad no se ejecutó (detonó) ningún adjunto ni se accedió a los enlaces contenidos en el mensaje." })]),
  bullet([new TextRun({ text: "Análisis asistido por agente. ", bold: true }), new TextRun({ text: "El presente borrador ha sido elaborado por un sistema automatizado (Veredictum) a partir de herramientas forenses. Los puntos no concluyentes se detallan en la sección 9 y requieren validación del perito antes de la emisión." })]),
];

/* ============================ 4. ANTECEDENTES ============================ */
const antecedentes = [
  H1("4. ANTECEDENTES"),
  P([new TextRun({ text: "Resumen del contexto. ", bold: true }), new TextRun({ text: `Se recibe para análisis el archivo ${C.evidencia || "de correo"}, correspondiente a un mensaje con asunto «${C.asunto || ""}» y remitente declarado «${C.remitente || ""}», reportado como sospechoso.` })]),
];

/* ============================ 5. RESUMEN EJECUTIVO ============================ */
const resumen = [
  H1("5. RESUMEN EJECUTIVO"),
  P([new TextRun({ text: "Veredicto: ", bold: true }), new TextRun({ text: `${N.veredicto || "—"} (confianza: ${N.nivel_confianza || "—"}).`, bold: true })]),
  ...(N.resumen ? [P(N.resumen)] : []),
  ...((N.resumen_bullets || []).map((b) => bullet(b))),
];

/* ============================ 6. NORMATIVA ============================ */
const normativa = [
  H1("6. NORMATIVA Y ESTÁNDARES APLICADOS"),
  tablecap("Marco normativo y estándares técnicos aplicados."),
  table(["Norma / Estándar", "Aplicación en este informe"], [
    ["ISO/IEC 27037:2012", "Identificación, recopilación, adquisición y preservación de evidencia digital."],
    ["UNE 71505 / 71506:2013", "Gestión y metodología de análisis forense de evidencias electrónicas."],
    ["RFC 5321 / 5322", "Protocolo SMTP y formato de los mensajes de correo (cabeceras)."],
    ["RFC 7208 (SPF) / 6376 (DKIM) / 7489 (DMARC)", "Mecanismos de autenticación del remitente de correo."],
    ["NIST SP 800-86", "Integración de técnicas forenses en la respuesta a incidentes."],
    ["LEC arts. 335-352 / LECrim arts. 456-485", "Regulación de la prueba pericial."],
  ], [3400, 5960]),
];

/* ============================ 7. METODOLOGÍA ============================ */
const metodologia = [
  H1("7. METODOLOGÍA Y HERRAMIENTAS"),
  P("Se aplicó una metodología de análisis estático, evitando la ejecución de cualquier artefacto y el acceso a recursos externos referenciados en el mensaje, priorizando la preservación de la integridad de la evidencia y la reproducibilidad de los resultados."),
  tablecap("Herramientas empleadas en el análisis."),
  table(["Herramienta", "Finalidad"], [
    ["Python 3 (módulo email)", "Análisis estructural MIME, extracción de cabeceras, cuerpo y adjuntos."],
    ["hashlib (SHA-256/SHA-1/MD5)", "Cálculo de funciones resumen para integridad e identificación."],
    ["oletools (olevba)", "Detección y extracción de macros VBA en documentos ofimáticos."],
    ["Identificación por números mágicos", "Determinación del tipo real de archivo, con independencia de la extensión."],
    ["VirusTotal", "Inteligencia de amenazas: correlación de hash y veredicto multimotor."],
  ], [3700, 5660]),
];

/* ============================ 8. DESARROLLO TÉCNICO ============================ */
function vtTexto(sha) {
  const v = (D.vt || {})[sha];
  if (!v) return "no consultado";
  if (v.estado === "consultado") return `${v.deteccion} detecciones`;
  if (v.estado === "no_consultado") return "no consultado (sin clave VT)";
  return "no encontrado / error";
}
const filasAdjuntos = (D.adjuntos || []).map((a) => [
  a.nombre || "—", a.tipo_real || "—", a.macros || "—",
  (a.sha256 || "").slice(0, 24) + "…", vtTexto(a.sha256)
]);
const desarrollo = [
  H1("8. DESARROLLO TÉCNICO"),
  H2("8.1. Preservación e identificación de la evidencia"),
  tablecap("Identificación e integridad del archivo de evidencia."),
  kv([
    ["Nombre del archivo", C.evidencia || "—"],
    ["Tamaño", `${C.tamano_bytes || "—"} bytes`],
    ["SHA-256", C.sha256 || "—"],
    ["MD5", C.md5 || "—"],
  ], 2700),
  spacer(),
  H2("8.2. Identidades y autenticación"),
  tablecap("Resultado de los mecanismos de autenticación del remitente."),
  table(["Mecanismo", "Resultado", "Lectura"], [
    ["SPF", AUTH.spf || "desconocido", (AUTH.spf === "pass") ? "El servidor de envío está autorizado por el dominio." : "El remitente no supera la verificación de origen."],
    ["DKIM", AUTH.dkim || "desconocido", (AUTH.dkim === "pass") ? "La firma criptográfica es válida." : "Ausencia o invalidez de firma."],
    ["DMARC", AUTH.dmarc || "desconocido", (AUTH.dmarc === "pass") ? "Alineación de dominios correcta." : "Sin política efectiva frente a suplantación."],
  ], [1600, 1700, 6060]),
  tablecap("Identidades declaradas en el mensaje."),
  kv([
    ["From (remitente)", C.remitente || "—"],
    ["Return-Path", C.return_path || "—"],
    ["Destinatario", C.destinatario || "—"],
    ["Fecha", C.fecha || "—"],
    ["Message-ID", C.message_id || "—"],
  ], 2700),
  spacer(),
  H2("8.3. Análisis de adjuntos"),
  ...((D.adjuntos || []).length
    ? [ tablecap("Caracterización de los archivos adjuntos."),
        table(["Nombre", "Tipo real", "Macros", "SHA-256", "VirusTotal"], filasAdjuntos, [2200, 1700, 1500, 2660, 1300]) ]
    : [ P("El mensaje no contiene archivos adjuntos.") ]),
  ...(() => {
    const filas = [];
    (D.adjuntos || []).forEach((a) => {
      ((a.yara || {}).coincidencias || []).forEach((c) =>
        filas.push([a.nombre, c.regla, c.descripcion || ""]));
    });
    return filas.length
      ? [tablecap("Coincidencias de reglas YARA en los adjuntos."),
         table(["Adjunto", "Regla YARA", "Descripción"], filas, [2200, 2600, 4560])]
      : [];
  })(),
  spacer(),
  H2("8.4. Hallazgos técnicos"),
  ...((N.hallazgos || []).length ? (N.hallazgos || []).map((h) => bullet(h)) : [P("Sin hallazgos técnicos adicionales.")]),
  ...((N.linea_temporal || []).length ? [H2("8.5. Línea temporal"), ...(N.linea_temporal || []).map((t) => bullet(t))] : []),
];

/* 8.6 Comportamiento dinámico (de los sandboxes de VirusTotal) */
const _comp = D.comportamiento || {};
const _compAdj = (D.adjuntos || []).map((a) => [a, _comp[a.sha256]]).filter(([, c]) => c && c.estado === "consultado");
if (_compAdj.length) {
  const _df = (x) => String(x).replace(/\./g, "[.]");
  desarrollo.push(H2("8.6. Comportamiento dinámico (sandbox de VirusTotal)"));
  desarrollo.push(P("Resumen del comportamiento del adjunto al ejecutarse, obtenido de la detonación realizada por los sandboxes de VirusTotal. El análisis local de Veredictum es estático: estos datos NO provienen de una ejecución en este entorno."));
  for (const [a, c] of _compAdj) {
    desarrollo.push(P([new TextRun({ text: `Adjunto: ${a.nombre} (${(a.sha256 || "").slice(0, 16)}…)`, bold: true })]));
    const secc = (titulo, items) => {
      if (!items || !items.length) return;
      desarrollo.push(P([new TextRun({ text: titulo, bold: true })]));
      items.forEach((it) => {
        const txt = typeof it === "string" ? it
          : (it.ruta ? `${it.ruta}${it.sha256 ? " (" + it.sha256.slice(0, 16) + "…)" : ""}` : JSON.stringify(it));
        desarrollo.push(bullet(txt));
      });
    };
    secc("Procesos creados:", c.procesos);
    secc("Ficheros soltados:", c.ficheros_soltados);
    secc("Cambios en el registro:", c.registro);
    secc("Conexiones de red (IPs):", (c.ips || []).map(_df));
    secc("Resoluciones DNS:", (c.dns || []).map(_df));
    secc("Técnicas MITRE ATT&CK:", c.mitre);
  }
}

/* 8.7 Análisis dinámico PROPIO (detonación en laboratorio aislado) */
const _det = D.detonacion || {};
if (_det.estado === "analizado") {
  const _dfn = (x) => String(x).replace(/\./g, "[.]");
  desarrollo.push(H2("8.7. Análisis dinámico propio (detonación en laboratorio aislado)"));
  desarrollo.push(P(`Comportamiento observado al ejecutar la muestra en un entorno aislado controlado por el perito. Fuente: ${_det.fuente || "monitorización local"}. La detonación se realizó sin acceso a Internet productivo; la evidencia original se preservó inalterada.`));
  const secD = (titulo, items, defang) => {
    if (!items || !items.length) return;
    desarrollo.push(P([new TextRun({ text: titulo, bold: true })]));
    (defang ? items.map(_dfn) : items).forEach((it) => desarrollo.push(bullet(String(it))));
  };
  secD("Procesos creados:", _det.procesos);
  secD("Ficheros escritos:", _det.ficheros_escritos);
  secD("Persistencia (claves de registro):", _det.persistencia);
  secD("Otros cambios en el registro:", _det.registro);
  secD("Conexiones de red:", _det.red, true);
}

/* ============================ 9. LIMITACIONES (INCERTIDUMBRES) ============================ */
const incert = [
  H1("9. LIMITACIONES DEL ANÁLISIS Y PUNTOS PARA VALIDACIÓN PERICIAL"),
  P("Esta sección recoge los puntos NO concluyentes detectados por el análisis automatizado. El perito debe verificarlos antes de emitir el dictamen; no constituyen conclusiones firmes."),
  ...((N.incertidumbres || []).length ? (N.incertidumbres || []).map((i) => bullet(i))
    : [P("El análisis no ha declarado incertidumbres. Aun así, el perito debe confirmar que la evidencia soporta todas las conclusiones.")]),
];

/* ============================ 10. IOCs ============================ */
const filasIoc = [];
(IOC.urls || []).forEach((u) => filasIoc.push(["URL", u.replace(/\./g, "[.]").replace(/^http/i, "hxxp")]));
(IOC.ips || []).forEach((i) => filasIoc.push(["IP", i.replace(/\./g, "[.]")]));
(IOC.dominios || []).forEach((d) => filasIoc.push(["Dominio", d.replace(/\./g, "[.]")]));
(IOC.correos || []).forEach((c) => filasIoc.push(["Correo", c.replace(/\./g, "[.]")]));
(D.adjuntos || []).forEach((a) => { if (a.sha256) filasIoc.push(["Hash adjunto", a.sha256]); });
const iocs = [
  H1("10. INDICADORES DE COMPROMISO (IoC)"),
  P("Se recopilan los indicadores extraídos para su bloqueo y vigilancia, neutralizados (defang) para evitar su activación accidental."),
  ...(filasIoc.length ? [tablecap("Relación de Indicadores de Compromiso identificados."), table(["Tipo", "Indicador"], filasIoc, [2200, 7160])]
    : [P("No se identificaron indicadores de compromiso.")]),
];

/* ============================ 11. CONCLUSIONES ============================ */
const ord = ["PRIMERA", "SEGUNDA", "TERCERA", "CUARTA", "QUINTA", "SEXTA", "SÉPTIMA", "OCTAVA", "NOVENA", "DÉCIMA"];
const conclusiones = [
  H1("11. CONCLUSIONES"),
  P("Como resultado de las actuaciones descritas, este perito concluye, con carácter de borrador sujeto a validación:"),
  ...((N.conclusiones || []).map((c, i) => new Paragraph({ spacing: { after: 60 },
    children: [new TextRun({ text: `${ord[i] || (i + 1) + "ª"}. `, bold: true }), new TextRun({ text: c })] }))),
  spacer(),
  H2("11.1. Recomendaciones"),
  ...((N.recomendaciones || []).length ? (N.recomendaciones || []).map((r) => bullet(r)) : [P("Sin recomendaciones.")]),
];

/* ============================ 12. CIERRE ============================ */
const cierre = [
  H1("12. CLÁUSULA DE CIERRE"),
  P("El presente borrador de informe pericial ha sido elaborado con base en la evidencia entregada, aplicando los principios técnicos y metodológicos de la informática forense. Queda sujeto a la revisión, validación y, en su caso, ratificación del perito firmante."),
  spacer(),
  P([new TextRun({ text: `En Málaga, a ${D.fecha_emision || ""}.` })]),
  spacer(),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Fdo.: Óscar Carretero Hilillo", bold: true })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Perito Informático Forense" })] }),
];

/* ============================ ANEXO I — CADENA DE CUSTODIA ============================ */
const anexo1 = [
  new Paragraph({ children: [new PageBreak()] }),
  H1("ANEXO I — REGISTRO DE CADENA DE CUSTODIA"),
  tablecap("Identificación e integridad de la evidencia digital."),
  kv([
    ["Nº de expediente", D.caso_id],
    ["ID de la evidencia", C.evidencia || "—"],
    ["Tamaño", `${C.tamano_bytes || "—"} bytes`],
    ["SHA-256", C.sha256 || "—"],
    ["MD5", C.md5 || "—"],
    ["Fecha de análisis", D.fecha_emision || "—"],
  ], 3400),
  spacer(),
  P("El análisis se realizó en estático sobre copia de la evidencia, verificada por hash; el archivo original se preservó inalterado. Ningún artefacto fue ejecutado."),
  spacer(),
  new Paragraph({ children: [new TextRun({ text: "Fdo.: Óscar Carretero Hilillo — Perito Informático Forense", bold: true })] }),
];

/* ============================ DOCUMENTO ============================ */
const doc = new Document({
  creator: "Veredictum",
  title: `Borrador de dictamen — ${D.caso_id}`,
  styles: {
    default: { document: { run: { font: "Arial", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: TEAL, space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 25, bold: true, font: "Arial", color: TEAL },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
    ]
  },
  numbering: { config: [
    { reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 280 } } } }] },
  ] },
  sections: [
    { properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      headers: { default: headerTLP }, footers: { default: footerStd }, children: portada },
    { properties: { type: SectionType.NEXT_PAGE, page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      headers: { default: headerTLP }, footers: { default: footerStd },
      children: [ ...indice, ...perito, ...objeto, ...alcance, ...antecedentes, ...resumen,
        ...normativa, ...metodologia, ...desarrollo, ...incert, ...iocs, ...conclusiones, ...cierre, ...anexo1 ] }
  ]
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log("OK -> " + OUT); });
