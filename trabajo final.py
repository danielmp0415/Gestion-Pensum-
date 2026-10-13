import os
import html
import json
import graphviz
from collections import defaultdict, deque
import webbrowser

class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.padres = []
        self.hijos = []

    def agregar_padre(self, padre):
        self.padres.append(padre)

    def agregar_hijo(self, hijo):
        self.hijos.append(hijo)

class Grafo:
    def __init__(self):
        self.nodos = {}

    def agregar_nodo(self, valor):
        nuevo_nodo = Nodo(valor)
        self.nodos[valor] = nuevo_nodo
        return nuevo_nodo

    def agregar_arista(self, padre, hijo):
        if padre not in self.nodos:
            self.agregar_nodo(padre)
        if hijo not in self.nodos:
            self.agregar_nodo(hijo)

        self.nodos[padre].agregar_hijo(hijo)
        self.nodos[hijo].agregar_padre(padre)

    def obtener_nodo(self, valor):
        return self.nodos.get(valor)

# Diccionario para asociar código con nombre completo
materias = {}
# Instancia del grafo
grafo_materias = Grafo()

# Carpeta donde se guardan los gráficos generados (.svg y .html)
CARPETA_GRAFICOS = 'graficos'


def ruta_grafico(nombre):
    """Devuelve la ruta del gráfico dentro de CARPETA_GRAFICOS, creando la carpeta si no existe"""
    os.makedirs(CARPETA_GRAFICOS, exist_ok=True)
    return os.path.join(CARPETA_GRAFICOS, nombre)

# Función para leer el archivo y construir el grafo
def leer_archivo(archivo):
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            for linea in f:
                partes = linea.strip().split(':')
                codigo_materia = partes[0].strip()
                nombre_materia = partes[1].strip()
                prerrequisitos_materia = partes[2].split(',') if len(partes) > 2 else []

                # Guardar el nombre de la materia
                materias[codigo_materia] = nombre_materia
                
                # Agregar nodos y aristas al grafo
                for pr in prerrequisitos_materia:
                    pr = pr.strip()
                    if pr:
                        grafo_materias.agregar_arista(pr, codigo_materia)

    except FileNotFoundError:
        print("Archivo no encontrado. Asegúrate de que la ruta es correcta.")
    except Exception as e:
        print(f"Ocurrió un error al leer el archivo: {e}")

def limpiar_consola():
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_pensum():
    if materias:
        print("\nPensum completo:")
        for codigo, nombre in materias.items():
            print(f"{codigo}: {nombre}")
    else:
        print("El pensum no ha sido cargado correctamente.")

def mostrar_prerrequisitos(materia):
    nodo = grafo_materias.obtener_nodo(materia)
    if nodo:
        print(f"\nPrerrequisitos para {materia} - {materias[materia]}:")
        if nodo.padres:
            for pr in nodo.padres:
                print(f"- {pr}: {materias.get(pr, 'Materia no encontrada')}")
        else:
            print("No tiene prerrequisitos.")
    else:
        print("Materia no encontrada.")

def obtener_prerrequisitos_indirectos(materia):
    nodo = grafo_materias.obtener_nodo(materia)
    if not nodo:
        return set()

    prerrequisitos = set()

    def explorar_prerrequisitos(nodo_actual):
        for padre in nodo_actual.padres:
            if padre not in prerrequisitos:
                prerrequisitos.add(padre)
                padre_nodo = grafo_materias.obtener_nodo(padre)
                if padre_nodo:
                    explorar_prerrequisitos(padre_nodo)

    explorar_prerrequisitos(nodo)
    return prerrequisitos

def obtener_dependientes_indirectos(materia):
    nodo = grafo_materias.obtener_nodo(materia)
    if not nodo:
        return set()

    dependientes = set()

    def explorar_dependientes(nodo_actual):
        for hijo in nodo_actual.hijos:
            if hijo not in dependientes:
                dependientes.add(hijo)
                hijo_nodo = grafo_materias.obtener_nodo(hijo)
                if hijo_nodo:
                    explorar_dependientes(hijo_nodo)

    explorar_dependientes(nodo)
    return dependientes

SIGLAS = {'I', 'II', 'III', 'IV', 'V', 'VI', 'TI', 'TIC', 'SQL', 'IA', 'UX', 'UI', 'ERP'}


def nombre_legible(nombre):
    """Pasa 'FISICA MECANICA II' a 'Fisica mecanica II' respetando siglas y números romanos"""
    if not nombre or nombre != nombre.upper():
        return nombre
    palabras = []
    for i, palabra in enumerate(nombre.lower().split()):
        if palabra.upper() in SIGLAS:
            palabra = palabra.upper()
        elif i == 0:
            palabra = palabra.capitalize()
        palabras.append(palabra)
    return ' '.join(palabras)


def generar_html_con_tooltips(svg_content, nombres, output_file, titulo='Pensum', resumen='', leyenda=None):
    """Genera un archivo HTML con el SVG, una leyenda y un panel de detalle por materia"""
    leyenda = leyenda or []
    svg_content = svg_content[svg_content.find('<svg'):]  # quitar el prólogo XML
    leyenda_html = ''.join(
        f'<li><span class="muestra muestra-{clase}"></span>{html.escape(texto)}</li>'
        for clase, texto in leyenda
    )

    plantilla = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITULO__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,600..800&display=swap" rel="stylesheet">
<style>
:root {
    --papel: #F5F7F6;
    --cuadricula: #DCE5E8;
    --punto: #C9D2D7;
    --tinta: #1F2B4D;
    --tinta-suave: #5A6582;
    --verde: #7FD48B;
    --verde-oscuro: #2E7D3E;
    --verde-claro: #D5F2D9;
    --linea-nivel: #A9B6C6;
    --grafito: #9298A2;
    --rojo: #C4312A;
    --blanco: #FFFFFF;
    --display: 'Bricolage Grotesque', 'Arial Narrow', sans-serif;
    --texto: 'Atkinson Hyperlegible', system-ui, sans-serif;
}
* { box-sizing: border-box; }
html, body { height: 100%; }
body {
    margin: 0;
    background: var(--papel);
    color: var(--tinta);
    font: 16px/1.5 var(--texto);
    display: grid;
    grid-template-rows: auto minmax(0, 1fr);
    grid-template-columns: minmax(0, 1fr);
}

/* Encabezado */
.encabezado {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 12px 40px;
    padding: 24px 32px 20px;
    border-bottom: 1px solid var(--cuadricula);
}
.encabezado h1 {
    margin: 0;
    font: 800 clamp(1.75rem, 4vw, 2.75rem)/1.05 var(--display);
    font-stretch: 80%;
    letter-spacing: -0.015em;
}
.resumen {
    margin: 6px 0 0;
    max-width: 60ch;
    color: var(--tinta-suave);
}
.leyenda {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 24px;
    margin: 0;
    padding: 0;
    list-style: none;
    font-size: 0.875rem;
}
.leyenda li { display: flex; align-items: center; gap: 8px; }
.muestra { display: inline-block; width: 34px; height: 16px; }
.muestra-disponible { background: var(--verde); border: 1px solid var(--verde-oscuro); border-radius: 4px; }
.muestra-no-abre { background: var(--verde-claro); border: 1px solid var(--verde-oscuro); border-radius: 4px; }
.muestra-bloqueada { border: 1.5px dashed var(--grafito); border-radius: 3px; }
.muestra-objetivo { border: 2.5px solid var(--rojo); border-radius: 3px; }
.muestra-ruta { height: 0; border-top: 2.5px solid var(--rojo); }

/* Área de trabajo */
.mesa { min-height: 0; min-width: 0; }
.lienzo {
    position: relative;
    height: 100%;
    overflow: hidden;
}
.hoja {
    height: 100%;
    overflow: auto;
    padding: 32px 32px 88px;  /* abajo deja sitio para los controles de zoom */
    background-color: var(--papel);
    background-image: radial-gradient(circle, var(--punto) 1px, transparent 1.5px);
    background-size: 22px 22px;
    background-attachment: local;
    cursor: grab;
    user-select: none;
    -webkit-user-select: none;
}
.hoja.arrastrando, .hoja.arrastrando .node { cursor: grabbing; }
.hoja svg { display: block; margin: 0 auto; height: auto; }

/* Grafo: los colores de Graphviz se sustituyen aquí */
.hoja svg > g > polygon { fill: transparent; stroke: none; }
.node path, .node polygon { fill: var(--blanco); stroke: var(--tinta); stroke-width: 1.2; }
.node text {
    font-family: var(--display);
    font-weight: 700;
    font-size: 14px;
    fill: var(--tinta);
}
.node { cursor: pointer; }
.node:focus { outline: none; }
.node:focus-visible path, .node:focus-visible polygon { stroke: var(--rojo); stroke-width: 3; }
.node.disponible path, .node.disponible polygon { fill: var(--verde); stroke: var(--verde-oscuro); stroke-width: 1; }
.node.no-abre path, .node.no-abre polygon { fill: var(--verde-claro); }
.node.bloqueada path, .node.bloqueada polygon {
    fill: var(--papel);
    stroke: var(--grafito);
    stroke-dasharray: 4 3;
}
.node.bloqueada text { fill: var(--tinta-suave); }
.node.objetivo path, .node.objetivo polygon { stroke: var(--rojo); stroke-width: 2.5; }
.node.objetivo text { fill: var(--rojo); }

.edge path { stroke: var(--tinta-suave); stroke-width: 1.4; }
.edge polygon { fill: var(--tinta-suave); stroke: var(--tinta-suave); }

.node, .edge { transition: opacity 180ms ease; }
.edge path, .edge polygon { transition: stroke 180ms ease, fill 180ms ease; }
svg.con-seleccion .node:not(.en-ruta) { opacity: 0.22; }
svg.con-seleccion .edge:not(.en-ruta) { opacity: 0.12; }
svg.con-seleccion .edge.antes path { stroke: var(--rojo); stroke-width: 2.2; }
svg.con-seleccion .edge.antes polygon { fill: var(--rojo); stroke: var(--rojo); }
svg.con-seleccion .edge.despues path { stroke: var(--tinta); stroke-width: 2.2; }
svg.con-seleccion .edge.despues polygon { fill: var(--tinta); stroke: var(--tinta); }
.node.seleccionada path, .node.seleccionada polygon { stroke: var(--rojo); stroke-width: 3; stroke-dasharray: none; }

/* Filas por trimestre (las dibuja el script) */
.niveles line { stroke: var(--linea-nivel); stroke-width: 1.5; }
.niveles line.sub { stroke-width: 1; stroke-dasharray: 5 5; }
.niveles .trimestre { font: 700 16px var(--display); fill: var(--tinta); }
.niveles .cuantas { font: 13px var(--texto); fill: var(--tinta-suave); }
svg.con-seleccion .niveles { opacity: 0.5; }

/* Zoom */
.zoom {
    position: absolute;
    right: 16px;
    transition: right 220ms ease;
    bottom: 16px;
    display: flex;
    border: 1px solid var(--tinta);
    border-radius: 6px;
    background: var(--blanco);
    overflow: hidden;
}
.zoom button {
    min-width: 44px;
    height: 40px;
    padding: 0 12px;
    border: 0;
    border-left: 1px solid var(--cuadricula);
    background: none;
    color: var(--tinta);
    font: 700 0.875rem var(--texto);
    cursor: pointer;
}
.zoom button:first-child { border-left: 0; }
.porcentaje {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 56px;
    border-left: 1px solid var(--cuadricula);
    font-size: 0.875rem;
    font-variant-numeric: tabular-nums;
    color: var(--tinta-suave);
}
.ayuda-zoom {
    position: absolute;
    left: 16px;
    bottom: 22px;
    margin: 0;
    font-size: 0.875rem;
    color: var(--tinta-suave);
}
.lienzo:fullscreen { background: var(--papel); }
.zoom button:hover { background: var(--papel); }
.zoom button:focus-visible, .lista button:focus-visible {
    outline: 2px solid var(--rojo);
    outline-offset: -2px;
}

/* Panel de detalle: solo aparece al elegir una materia */
.panel {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    z-index: 5;
    width: 360px;
    padding: 28px 24px;
    overflow-y: auto;
    background: var(--blanco);
    border-left: 1px solid var(--cuadricula);
    box-shadow: -16px 0 40px rgba(31, 43, 77, 0.10);
    transform: translateX(100%);
    visibility: hidden;
    transition: transform 220ms ease, visibility 0s linear 220ms;
}
.panel.abierto {
    transform: none;
    visibility: visible;
    transition: transform 220ms ease;
}
.lienzo.con-panel .zoom { right: 376px; }
.cerrar {
    position: absolute;
    top: 16px;
    right: 16px;
    height: 36px;
    padding: 0 12px;
    border: 1px solid var(--cuadricula);
    border-radius: 6px;
    background: var(--blanco);
    color: var(--tinta);
    font: 700 0.875rem var(--texto);
    cursor: pointer;
}
.cerrar:hover { background: var(--papel); }
.cerrar:focus-visible { outline: 2px solid var(--rojo); outline-offset: 2px; }
.codigo-fila {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 14px;
    margin-top: 36px;  /* deja libre la esquina del botón Cerrar */
}
.copiar {
    height: 32px;
    padding: 0 12px;
    border: 1px solid var(--tinta);
    border-radius: 6px;
    background: var(--blanco);
    color: var(--tinta);
    font: 700 0.875rem var(--texto);
    cursor: pointer;
}
.copiar:hover { background: var(--papel); }
.copiar:focus-visible { outline: 2px solid var(--rojo); outline-offset: 2px; }
.copiar.hecho { background: var(--verde-claro); border-color: var(--verde-oscuro); color: var(--verde-oscuro); }
.panel h2 {
    margin: 0;
    font: 800 2.25rem/1 var(--display);
    font-stretch: 80%;
    letter-spacing: -0.01em;
}
.panel .nombre { margin: 8px 0 0; font-size: 1.3125rem; line-height: 1.3; }
.estado {
    display: inline-block;
    margin-top: 14px;
    padding: 2px 8px;
    font-size: 0.875rem;
    font-weight: 700;
}
.estado.disponible { background: var(--verde); }
.estado.bloqueada { border: 1.5px dashed var(--grafito); color: var(--tinta-suave); }
.panel h3 {
    margin: 28px 0 8px;
    font-size: 0.875rem;
    font-weight: 700;
    color: var(--tinta-suave);
}
.panel h3.antes { color: var(--rojo); }
.lista { margin: 0; padding: 0; list-style: none; }
.lista button {
    display: grid;
    grid-template-columns: 72px 1fr;
    gap: 8px;
    width: 100%;
    padding: 8px 0;
    border: 0;
    border-top: 1px solid var(--cuadricula);
    background: none;
    color: var(--tinta);
    font: 0.875rem/1.35 var(--texto);
    text-align: left;
    cursor: pointer;
}
.lista button:hover .cod { text-decoration: underline; }
.lista .cod { font-family: var(--display); font-weight: 700; }
.ninguna { margin: 0; font-size: 0.875rem; color: var(--tinta-suave); }

/* Etiqueta flotante al pasar el cursor */
.etiqueta {
    position: fixed;
    z-index: 10;
    max-width: 260px;
    padding: 6px 10px;
    border-radius: 4px;
    background: var(--tinta);
    color: var(--papel);
    font-size: 0.875rem;
    pointer-events: none;
    display: none;
}
.etiqueta.visible { display: block; }

@media (max-width: 760px) {
    body { height: auto; display: block; }
    .encabezado { padding: 20px 16px 16px; }
    .lienzo { height: 75vh; }
    .hoja { padding: 16px 16px 72px; }
    .ayuda-zoom, #completa { display: none; }
    .panel {
        top: auto;
        left: 0;
        width: auto;
        max-height: 70%;
        padding: 24px 16px 32px;
        border-left: 0;
        border-top: 1px solid var(--cuadricula);
        border-radius: 12px 12px 0 0;
        box-shadow: 0 -16px 40px rgba(31, 43, 77, 0.12);
        transform: translateY(100%);
    }
    .lienzo.con-panel .zoom { right: 16px; }
}
@media (prefers-reduced-motion: reduce) {
    .node, .edge, .edge path, .edge polygon, .panel, .zoom { transition: none; }
}
</style>
</head>
<body>
<header class="encabezado">
    <div>
        <h1>__TITULO__</h1>
        <p class="resumen">__RESUMEN__</p>
    </div>
    <ul class="leyenda">__LEYENDA__</ul>
</header>
<main class="mesa">
    <div class="lienzo">
        <div class="hoja" id="hoja">__SVG__</div>
        <p class="ayuda-zoom">Arrastra para moverte. Pellizca o usa Ctrl + rueda para hacer zoom</p>
        <div class="zoom" role="group" aria-label="Zoom del gráfico">
            <button type="button" data-zoom="-1" aria-label="Alejar" title="Alejar (tecla −)">−</button>
            <span class="porcentaje" id="porcentaje" aria-live="polite">100%</span>
            <button type="button" data-zoom="1" aria-label="Acercar" title="Acercar (tecla +)">+</button>
            <button type="button" data-zoom="0" title="Ver todo el gráfico (tecla 0)">Ver todo</button>
            <button type="button" id="completa" title="Pantalla completa (tecla F)">Pantalla completa</button>
        </div>
        <aside class="panel" id="panel" aria-live="polite" aria-label="Detalle de la materia">
            <button type="button" class="cerrar" id="cerrar">Cerrar</button>
            <div id="detalle"></div>
        </aside>
    </div>
</main>
<div class="etiqueta" id="etiqueta"></div>
<script>
const nombres = __NOMBRES__;
const hoja = document.getElementById('hoja');
const svg = hoja.querySelector('svg');
const lienzo = document.querySelector('.lienzo');
const panel = document.getElementById('panel');
const detalle = document.getElementById('detalle');
const etiqueta = document.getElementById('etiqueta');

const nodos = {};
const padres = {};
const hijos = {};
const aristas = [];

svg.querySelectorAll('.node').forEach(g => {
    const cod = g.querySelector('title').textContent.trim();
    nodos[cod] = g;
    padres[cod] = [];
    hijos[cod] = [];
    g.setAttribute('tabindex', '0');
    g.setAttribute('role', 'button');
    g.setAttribute('aria-label', cod + ': ' + (nombres[cod] || ''));
    g.querySelector('title').remove();  // evita el tooltip nativo del navegador
    g.dataset.cod = cod;
});
svg.querySelectorAll('.edge').forEach(g => {
    if (!g.querySelector('path')) { g.remove(); return; }  // aristas invisibles que solo ordenan filas
    const [de, a] = g.querySelector('title').textContent.split('->').map(s => s.trim());
    g.querySelector('title').remove();
    aristas.push({ g, de, a });
    if (padres[a]) padres[a].push(de);
    if (hijos[de]) hijos[de].push(a);
});

function recorrer(cod, mapa, vistos = new Set()) {
    for (const otro of mapa[cod] || []) {
        if (!vistos.has(otro)) { vistos.add(otro); recorrer(otro, mapa, vistos); }
    }
    return vistos;
}

function nivelDe(g) {
    const m = (g.getAttribute('class') || '').match(/nivel-(\d+)/);
    return m ? Number(m[1]) : null;
}

function estadoDe(g) {
    if (g.classList.contains('disponible')) {
        return ['disponible', g.classList.contains('no-abre')
            ? 'Puedes inscribirla ahora; no abre otras materias'
            : 'Puedes inscribirla ahora'];
    }
    if (g.classList.contains('bloqueada')) {
        const n = nivelDe(g);
        return ['bloqueada', n ? 'Disponible desde el trimestre ' + (n - 1)
                                : 'Bloqueada por prerrequisitos pendientes'];
    }
    return null;
}

function lista(codigos) {
    if (!codigos.length) return null;
    const ul = document.createElement('ul');
    ul.className = 'lista';
    codigos.forEach(cod => {
        const li = document.createElement('li');
        const b = document.createElement('button');
        b.type = 'button';
        const c = document.createElement('span');
        c.className = 'cod';
        c.textContent = cod;
        const n = document.createElement('span');
        n.textContent = nombres[cod] || '';
        b.append(c, n);
        b.addEventListener('click', () => { seleccionar(cod); nodos[cod].focus(); });
        li.append(b);
        ul.append(li);
    });
    return ul;
}

function seccion(texto, clase, codigos, siVacio) {
    const h = document.createElement('h3');
    h.textContent = texto;
    if (clase) h.className = clase;
    const contenido = lista(codigos);
    if (contenido) return [h, contenido];
    const p = document.createElement('p');
    p.className = 'ninguna';
    p.textContent = siVacio;
    return [h, p];
}

let seleccion = null;

async function copiarCodigo(cod, boton) {
    let ok = false;
    try {
        await navigator.clipboard.writeText(cod);
        ok = true;
    } catch (e) {
        // Respaldo para navegadores que no permiten el portapapeles en archivos locales
        const area = document.createElement('textarea');
        area.value = cod;
        area.style.position = 'fixed';
        area.style.opacity = '0';
        document.body.append(area);
        area.select();
        try { ok = document.execCommand('copy'); } catch (e2) { ok = false; }
        area.remove();
    }
    boton.textContent = ok ? 'Copiado' : 'No se pudo copiar';
    boton.classList.toggle('hecho', ok);
    clearTimeout(boton._temporizador);
    boton._temporizador = setTimeout(() => {
        boton.textContent = 'Copiar código';
        boton.classList.remove('hecho');
    }, 1600);
}

function limpiar() {
    seleccion = null;
    svg.classList.remove('con-seleccion');
    svg.querySelectorAll('.en-ruta, .seleccionada, .antes, .despues')
        .forEach(el => el.classList.remove('en-ruta', 'seleccionada', 'antes', 'despues'));
    panel.classList.remove('abierto');
    lienzo.classList.remove('con-panel');
}

function seleccionar(cod) {
    if (seleccion === cod) { limpiar(); return; }
    limpiar();
    seleccion = cod;
    const antes = recorrer(cod, padres);
    const despues = recorrer(cod, hijos);

    svg.classList.add('con-seleccion');
    nodos[cod].classList.add('en-ruta', 'seleccionada');
    antes.forEach(c => nodos[c] && nodos[c].classList.add('en-ruta'));
    despues.forEach(c => nodos[c] && nodos[c].classList.add('en-ruta'));
    aristas.forEach(({ g, de, a }) => {
        if ((antes.has(de) || de === cod) && (antes.has(a) || a === cod)) g.classList.add('en-ruta', 'antes');
        else if ((despues.has(a)) && (despues.has(de) || de === cod)) g.classList.add('en-ruta', 'despues');
    });

    detalle.innerHTML = '';
    const h2 = document.createElement('h2');
    h2.textContent = cod;
    const copiar = document.createElement('button');
    copiar.type = 'button';
    copiar.className = 'copiar';
    copiar.textContent = 'Copiar código';
    copiar.addEventListener('click', () => copiarCodigo(cod, copiar));
    const fila = document.createElement('div');
    fila.className = 'codigo-fila';
    fila.append(h2, copiar);
    const nombre = document.createElement('p');
    nombre.className = 'nombre';
    nombre.textContent = nombres[cod] || 'Sin nombre';
    detalle.append(fila, nombre);
    const estado = estadoDe(nodos[cod]);
    if (estado) {
        const s = document.createElement('span');
        s.className = 'estado ' + estado[0];
        s.textContent = estado[1];
        detalle.append(s);
    }
    detalle.append(...seccion('Necesitas aprobar antes', 'antes', padres[cod],
                              'Nada de lo que aparece aquí.'));
    detalle.append(...seccion('Te abre después', '', hijos[cod],
                              'No desbloquea ninguna materia de este gráfico.'));
    panel.scrollTop = 0;
    panel.classList.add('abierto');
    lienzo.classList.add('con-panel');
}

Object.entries(nodos).forEach(([cod, g]) => {
    g.addEventListener('click', e => {
        e.stopPropagation();
        if (e.pointerType === 'touch') etiqueta.classList.remove('visible');
        seleccionar(cod);
    });
    g.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); seleccionar(cod); }
    });
    g.addEventListener('mouseenter', () => {
        if (!nombres[cod]) return;
        etiqueta.textContent = nombres[cod];
        etiqueta.classList.add('visible');
    });
    g.addEventListener('mousemove', e => {
        // Sin salirse de la ventana por la derecha ni por abajo
        const ancho = etiqueta.offsetWidth, alto = etiqueta.offsetHeight;
        etiqueta.style.left = Math.min(e.clientX + 14, innerWidth - ancho - 8) + 'px';
        etiqueta.style.top = (e.clientY + 14 + alto > innerHeight ? e.clientY - alto - 10 : e.clientY + 14) + 'px';
    });
    g.addEventListener('mouseleave', () => etiqueta.classList.remove('visible'));
});
hoja.addEventListener('click', limpiar);
document.getElementById('cerrar').addEventListener('click', limpiar);
document.addEventListener('keydown', e => { if (e.key === 'Escape') limpiar(); });

// Arrastrar con clic izquierdo para desplazarse por el gráfico
let arrastre = null;
let huboArrastre = false;
hoja.addEventListener('pointerdown', e => {
    if (e.button !== 0 || e.pointerType === 'touch') return;  // en táctil ya se desplaza con el dedo
    arrastre = { x: e.clientX, y: e.clientY, izq: hoja.scrollLeft, arriba: hoja.scrollTop, id: e.pointerId };
    huboArrastre = false;
});
hoja.addEventListener('pointermove', e => {
    if (!arrastre) return;
    const dx = e.clientX - arrastre.x;
    const dy = e.clientY - arrastre.y;
    if (!huboArrastre) {
        if (Math.hypot(dx, dy) < 5) return;  // por debajo de esto sigue contando como clic
        huboArrastre = true;
        hoja.setPointerCapture(arrastre.id);
        hoja.classList.add('arrastrando');
        etiqueta.classList.remove('visible');
    }
    hoja.scrollLeft = arrastre.izq - dx;
    hoja.scrollTop = arrastre.arriba - dy;
});
function soltar() {
    arrastre = null;
    hoja.classList.remove('arrastrando');
}
hoja.addEventListener('pointerup', soltar);
hoja.addEventListener('pointercancel', soltar);
// Si hubo arrastre, el clic que llega al soltar no debe elegir ni cerrar nada
hoja.addEventListener('click', e => {
    if (huboArrastre) { e.stopPropagation(); huboArrastre = false; }
}, true);

// Filas por trimestre: los nodos traen la clase nivel-N desde Python.
// El nivel 1 es el trimestre actual (trimestre 0), el nivel 2 es el trimestre 1, etc.
function nombreTrimestre(n) {
    return n === 1 ? 'Trimestre 0 (actual)' : 'Trimestre ' + (n - 1);
}
function plural(k, uno, varios) { return k + ' ' + (k === 1 ? uno : varios); }

const filas = {};
Object.values(nodos).forEach(g => {
    const n = nivelDe(g);
    if (n) (filas[n] = filas[n] || []).push(g);
});
const numerosNivel = Object.keys(filas).map(Number).sort((a, b) => a - b);
if (numerosNivel.length) {
    const ns = 'http://www.w3.org/2000/svg';
    const capa = svg.querySelector('g.graph');
    const caja = capa.getBBox();
    const izq = caja.x - 175;
    const der = caja.x + caja.width;
    const medir = nodosFila => {
        const cajas = nodosFila.map(g => g.getBBox());
        return {
            arriba: Math.min(...cajas.map(b => b.y)),
            abajo: Math.max(...cajas.map(b => b.y + b.height)),
            centro: cajas.reduce((m, b) => Math.min(m, b.y + b.height / 2), Infinity),
        };
    };
    const linea = (y, clase) => {
        const l = document.createElementNS(ns, 'line');
        l.setAttribute('x1', izq);
        l.setAttribute('x2', der);
        l.setAttribute('y1', y);
        l.setAttribute('y2', y);
        if (clase) l.setAttribute('class', clase);
        return l;
    };
    const tspan = (clase, texto, dy) => {
        const t = document.createElementNS(ns, 'tspan');
        t.setAttribute('class', clase);
        t.setAttribute('x', izq);
        if (dy) t.setAttribute('dy', dy);
        t.textContent = texto;
        return t;
    };

    const grupo = document.createElementNS(ns, 'g');
    grupo.setAttribute('class', 'niveles');
    let anterior = null;
    numerosNivel.forEach(n => {
        // En el trimestre actual se distinguen las que no abren nada de las que sí abren
        let subgrupos = [{ nodos: filas[n], texto: plural(filas[n].length, 'materia', 'materias') }];
        if (n === 1) {
            const noAbren = filas[n].filter(g => g.classList.contains('no-abre'));
            const abren = filas[n].filter(g => !g.classList.contains('no-abre'));
            subgrupos = [
                { nodos: noAbren, texto: plural(noAbren.length, 'no abre otras', 'no abren otras') },
                { nodos: abren, texto: plural(abren.length, 'abre otras', 'abren otras') },
            ].filter(sg => sg.nodos.length);
        }
        const medidas = subgrupos.map(sg => medir(sg.nodos));
        const franja = {
            arriba: Math.min(...medidas.map(m => m.arriba)),
            abajo: Math.max(...medidas.map(m => m.abajo)),
        };
        if (anterior) grupo.append(linea((anterior.abajo + franja.arriba) / 2));
        subgrupos.forEach((sg, k) => {
            if (k > 0) grupo.append(linea((medidas[k - 1].abajo + medidas[k].arriba) / 2, 'sub'));
            const texto = document.createElementNS(ns, 'text');
            if (k === 0) {
                texto.setAttribute('y', medidas[k].centro - 2);
                texto.append(tspan('trimestre', nombreTrimestre(n)), tspan('cuantas', sg.texto, '17'));
            } else {
                texto.setAttribute('y', medidas[k].centro + 5);
                texto.append(tspan('cuantas', sg.texto));
            }
            grupo.append(texto);
        });
        anterior = franja;
    });
    const fondo = capa.querySelector(':scope > polygon');
    capa.insertBefore(grupo, fondo ? fondo.nextSibling : capa.firstChild);
    // Amplía el viewBox para que quepan las etiquetas de la izquierda
    const vb = svg.viewBox.baseVal;
    const desplazamiento = capa.transform.baseVal.consolidate().matrix.e;
    const nueva = capa.getBBox();
    svg.setAttribute('viewBox', `${nueva.x + desplazamiento - 8} ${vb.y} ${nueva.width + 16} ${vb.height}`);
}

// Zoom: el tamaño natural del SVG viene de su viewBox
const porcentaje = document.getElementById('porcentaje');
const anchoNatural = svg.viewBox.baseVal.width;
const altoNatural = svg.viewBox.baseVal.height;
svg.removeAttribute('width');
svg.removeAttribute('height');
let escala = 1;
let ajustado = true;  // mientras sea true, el gráfico se reajusta si cambia el tamaño

function aplicar(nueva, cx, cy) {
    ajustado = false;
    nueva = Math.max(0.2, Math.min(4, nueva));
    // Mantiene fijo el punto bajo el cursor (o el centro) al cambiar la escala
    const r = hoja.getBoundingClientRect();
    const px = cx === undefined ? r.width / 2 : cx - r.left;
    const py = cy === undefined ? r.height / 2 : cy - r.top;
    const x = (hoja.scrollLeft + px) / escala;
    const y = (hoja.scrollTop + py) / escala;
    escala = nueva;
    svg.style.width = (anchoNatural * escala) + 'px';
    hoja.scrollLeft = x * escala - px;
    hoja.scrollTop = y * escala - py;
    porcentaje.textContent = Math.round(escala * 100) + '%';
}
function verTodo() {
    ajustado = true;
    const estilo = getComputedStyle(hoja);
    const rellenoX = parseFloat(estilo.paddingLeft) + parseFloat(estilo.paddingRight);
    const rellenoY = parseFloat(estilo.paddingTop) + parseFloat(estilo.paddingBottom);
    escala = Math.min((hoja.clientWidth - rellenoX) / anchoNatural,
                      (hoja.clientHeight - rellenoY) / altoNatural, 1.5);
    svg.style.width = (anchoNatural * escala) + 'px';
    hoja.scrollTo(0, 0);
    porcentaje.textContent = Math.round(escala * 100) + '%';
}

document.querySelectorAll('[data-zoom]').forEach(b => b.addEventListener('click', () => {
    const paso = Number(b.dataset.zoom);
    if (paso === 0) verTodo();
    else aplicar(escala * (paso > 0 ? 1.25 : 0.8));
}));
// Pellizco del trackpad y Ctrl + rueda
hoja.addEventListener('wheel', e => {
    if (!e.ctrlKey && !e.metaKey) return;
    e.preventDefault();
    aplicar(escala * Math.exp(-e.deltaY * 0.01), e.clientX, e.clientY);
}, { passive: false });

const botonCompleta = document.getElementById('completa');
function alternarCompleta() {
    if (document.fullscreenElement) document.exitFullscreen();
    else if (lienzo.requestFullscreen) lienzo.requestFullscreen();
}
botonCompleta.addEventListener('click', alternarCompleta);
document.addEventListener('fullscreenchange', () => {
    botonCompleta.textContent = document.fullscreenElement ? 'Salir' : 'Pantalla completa';
    requestAnimationFrame(verTodo);
});
document.addEventListener('keydown', e => {
    if (e.target.closest && e.target.closest('input, textarea')) return;
    if (e.key === '+' || e.key === '=') aplicar(escala * 1.25);
    else if (e.key === '-') aplicar(escala * 0.8);
    else if (e.key === '0') verTodo();
    else if (e.key === 'f' || e.key === 'F') alternarCompleta();
});
new ResizeObserver(() => { if (ajustado) verTodo(); }).observe(hoja);
verTodo();
</script>
</body>
</html>"""

    contenido = (plantilla
                 .replace('__TITULO__', html.escape(titulo))
                 .replace('__RESUMEN__', html.escape(resumen))
                 .replace('__LEYENDA__', leyenda_html)
                 .replace('__NOMBRES__', json.dumps({c: nombre_legible(n) for c, n in nombres.items()},
                                                    ensure_ascii=False))
                 .replace('__SVG__', svg_content))

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(contenido)


def graficar_prerrequisitos_graphviz(materia):
    nodo = grafo_materias.obtener_nodo(materia)
    if not nodo:
        print("Materia no encontrada.")
        return
    
    prerrequisitos = obtener_prerrequisitos_indirectos(materia)
    
    if not prerrequisitos:
        print(f"La materia {materia} no tiene prerrequisitos para graficar.")
        return
    
    # Crear grafo de Graphviz
    dot = graphviz.Digraph(comment=f'Prerrequisitos de {materia}')
    dot.attr(rankdir='TB')  # Top to Bottom
    dot.attr('node', shape='box', style='filled,rounded', fillcolor='lightgreen', 
             fontname='Arial', fontsize='14', margin='0.18,0.08')
    dot.attr('edge', color='#555555', penwidth='1.4', arrowsize='0.7')
    dot.attr(splines='line')  # Líneas rectas
    dot.attr(bgcolor='transparent')
    
    visitados = set()
    tooltips = {}

    def agregar_nodos_recursivo(nodo_actual):
        if nodo_actual.valor in visitados:
            return
        visitados.add(nodo_actual.valor)
        
        # Agregar nodo con solo el código
        dot.node(nodo_actual.valor, nodo_actual.valor)
        tooltips[nodo_actual.valor] = materias.get(nodo_actual.valor, 'Sin nombre')
        
        # Agregar aristas
        for padre in nodo_actual.padres:
            dot.edge(padre, nodo_actual.valor)
            padre_nodo = grafo_materias.obtener_nodo(padre)
            if padre_nodo:
                agregar_nodos_recursivo(padre_nodo)

    agregar_nodos_recursivo(nodo)
    
    # Resaltar la materia objetivo
    dot.node(materia, materia, **{'class': 'objetivo'})
    
    # Generar SVG
    output_name = ruta_grafico(f'prerrequisitos_{materia}')
    dot.render(output_name, format='svg', cleanup=True)
    
    # Leer SVG y crear HTML con tooltips
    with open(f'{output_name}.svg', 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    html_file = f'{output_name}.html'
    generar_html_con_tooltips(
        svg_content, tooltips, html_file,
        titulo=f'Antes de {materia}',
        resumen=f'Todo lo que hay que aprobar antes de {materia} ({nombre_legible(materias.get(materia, "sin nombre"))}).',
        leyenda=[('objetivo', materia), ('ruta', 'Prerrequisito de la materia que elijas')],
    )
    
    # Abrir en navegador
    webbrowser.open(f'file://{os.path.abspath(html_file)}')
    print(f"✅ Gráfico generado: {html_file}")

def graficar_dependientes_graphviz(materia):
    nodo = grafo_materias.obtener_nodo(materia)
    if not nodo:
        print("Materia no encontrada.")
        return

    dependientes = obtener_dependientes_indirectos(materia)
    
    if not dependientes:
        print("Esta materia no tiene dependientes para graficar.")
        return

    # Crear grafo de Graphviz
    dot = graphviz.Digraph(comment=f'Dependientes de {materia}')
    dot.attr(rankdir='TB')
    dot.attr('node', shape='box', style='filled,rounded', fillcolor='lightcoral',
             fontname='Arial', fontsize='14', margin='0.18,0.08')
    dot.attr('edge', color='#555555', penwidth='1.4', arrowsize='0.7')
    dot.attr(splines='line')  # Líneas rectas
    dot.attr(bgcolor='transparent')
    
    visitados = set()
    tooltips = {}

    def agregar_nodos_recursivo(nodo_actual):
        if nodo_actual.valor in visitados:
            return
        visitados.add(nodo_actual.valor)
        
        dot.node(nodo_actual.valor, nodo_actual.valor)
        tooltips[nodo_actual.valor] = materias.get(nodo_actual.valor, 'Sin nombre')
        
        for hijo in nodo_actual.hijos:
            dot.edge(nodo_actual.valor, hijo)
            hijo_nodo = grafo_materias.obtener_nodo(hijo)
            if hijo_nodo:
                agregar_nodos_recursivo(hijo_nodo)

    agregar_nodos_recursivo(nodo)
    
    # Resaltar la materia objetivo
    dot.node(materia, materia, **{'class': 'objetivo'})
    
    # Generar SVG y HTML
    output_name = ruta_grafico(f'dependientes_{materia}')
    dot.render(output_name, format='svg', cleanup=True)
    
    with open(f'{output_name}.svg', 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    html_file = f'{output_name}.html'
    generar_html_con_tooltips(
        svg_content, tooltips, html_file,
        titulo=f'Lo que abre {materia}',
        resumen=f'Materias que se desbloquean, directa o indirectamente, al aprobar {materia} ({nombre_legible(materias.get(materia, "sin nombre"))}).',
        leyenda=[('objetivo', materia), ('ruta', 'Prerrequisito de la materia que elijas')],
    )
    
    webbrowser.open(f'file://{os.path.abspath(html_file)}')
    print(f"✅ Gráfico generado: {html_file}")

def graficar_materias_no_cursadas_graphviz(ruta_no_cursadas):
    """Grafica las materias no cursadas con Graphviz"""
    try:
        materias_no_cursadas = {}
        with open(ruta_no_cursadas, 'r', encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                if linea:
                    partes = linea.split(':')
                    if len(partes) >= 3:
                        codigo = partes[0].strip()
                        nombre = partes[1].strip()
                        prereqs_str = partes[2].strip()
                        
                        prerrequisitos = []
                        if prereqs_str:
                            prerrequisitos = [p.strip() for p in prereqs_str.split(',') if p.strip()]
                        
                        materias_no_cursadas[codigo] = {
                            'nombre': nombre,
                            'prerrequisitos': prerrequisitos
                        }
        
        if not materias_no_cursadas:
            print("No hay materias no cursadas para graficar.")
            return
        
        # Crear grafo
        dot = graphviz.Digraph(comment='Materias No Cursadas')
        dot.attr(rankdir='TB')
        dot.attr('node', shape='box', style='filled,rounded', fontname='Arial', fontsize='14',
                 margin='0.18,0.08')
        dot.attr('edge', color='#555555', penwidth='1.4', arrowsize='0.7')
        dot.attr(splines='line')  # Líneas rectas
        dot.attr(nodesep='0.25', ranksep='0.7')
        dot.attr(bgcolor='transparent')

        materias_disponibles = []
        materias_bloqueadas = []
        tooltips = {}

        # Nivel = trimestre más temprano en que se puede dar la materia:
        # 1 si no tiene prerrequisitos pendientes; si no, 1 + el nivel de su prerrequisito más tardío
        niveles = {}

        def calcular_nivel(codigo, en_camino=()):
            if codigo not in niveles:
                pendientes = [p for p in materias_no_cursadas[codigo]['prerrequisitos']
                              if p in materias_no_cursadas and p not in en_camino]
                niveles[codigo] = 1 + max((calcular_nivel(p, en_camino + (codigo,)) for p in pendientes),
                                          default=0)
            return niveles[codigo]

        for codigo in materias_no_cursadas:
            calcular_nivel(codigo)

        # Clasificar materias; cada nivel va en su propia franja del gráfico
        por_nivel = defaultdict(list)
        for codigo in materias_no_cursadas:
            por_nivel[niveles[codigo]].append(codigo)

        # En el trimestre actual se separan las materias que abren otras de las que no abren
        # ninguna: las que no abren van en renglones propios arriba (partidos si son muchas) y
        # las que abren quedan en el renglón de abajo, pegadas a lo que desbloquean
        abren_algo = {p for info in materias_no_cursadas.values()
                      for p in info['prerrequisitos'] if p in materias_no_cursadas}
        ancho = max([len(c) for n, c in por_nivel.items() if n > 1] + [8])
        primero = por_nivel[1]
        conectadas = [c for c in primero if c in abren_algo]
        sueltas = [c for c in primero if c not in abren_algo]
        renglones = [sueltas[i:i + ancho] for i in range(0, len(sueltas), ancho)]
        if conectadas:
            renglones.append(conectadas)

        filas = [(1, r) for r in renglones] + [(n, por_nivel[n]) for n in sorted(por_nivel) if n > 1]
        for i, (nivel, codigos) in enumerate(filas):
            with dot.subgraph(name=f'fila_{i}') as fila:
                fila.attr(rank='same')
                for codigo in codigos:
                    tooltips[codigo] = materias_no_cursadas[codigo]['nombre']
                    if nivel == 1:
                        materias_disponibles.append(codigo)
                        abre = 'abre' if codigo in abren_algo else 'no-abre'
                        fila.node(codigo, codigo, **{'class': f'disponible {abre} nivel-{nivel}'})
                    else:
                        materias_bloqueadas.append(codigo)
                        fila.node(codigo, codigo, **{'class': f'bloqueada nivel-{nivel}'})
        # Aristas invisibles para apilar los renglones extra del primer nivel en orden
        for arriba, abajo in zip(renglones, renglones[1:]):
            dot.edge(arriba[0], abajo[0], style='invis')
        
        # Agregar aristas
        for codigo, info in materias_no_cursadas.items():
            for prereq in info['prerrequisitos']:
                if prereq in materias_no_cursadas:
                    dot.edge(prereq, codigo)
        
        print(f"✅ Materias disponibles: {len(materias_disponibles)}")
        print(f"🔒 Materias bloqueadas: {len(materias_bloqueadas)}")
        
        # Generar SVG y HTML
        output_name = ruta_grafico('materias_no_cursadas')
        dot.render(output_name, format='svg', cleanup=True)
        
        with open(f'{output_name}.svg', 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        html_file = f'{output_name}.html'
        generar_html_con_tooltips(
            svg_content, tooltips, html_file,
            titulo='Materias pendientes',
            resumen=f'Te faltan {len(materias_no_cursadas)} materias. Cada franja es un trimestre: '
                    f'arriba el actual, con las {len(materias_disponibles)} que puedes inscribir ya, y debajo '
                    f'lo que se abre al aprobarlas. Como mínimo te quedan {max(niveles.values())} '
                    f'trimestres contando el actual.',
            leyenda=[('disponible', 'Disponible, abre otras'), ('no-abre', 'Disponible, no abre otras'),
                     ('bloqueada', 'Bloqueada'), ('ruta', 'Prerrequisito de la materia que elijas')],
        )
        
        webbrowser.open(f'file://{os.path.abspath(html_file)}')
        print(f"✅ Gráfico generado: {html_file}")
        
        mostrar_analisis_detallado(materias_disponibles, materias_bloqueadas, materias_no_cursadas)
        
    except FileNotFoundError:
        print("❌ Archivo de materias no cursadas no encontrado.")
    except Exception as e:
        print(f"❌ Error al crear el gráfico: {e}")
        import traceback
        traceback.print_exc()

def mostrar_analisis_detallado(disponibles, bloqueadas, materias_info):
    """Muestra análisis detallado de las materias"""
    print(f"\n{'='*80}")
    print("📚 ANÁLISIS DETALLADO DE MATERIAS PENDIENTES")
    print(f"{'='*80}")
    
    total = len(materias_info)
    print(f"📊 Total de materias pendientes: {total}")
    print(f"✅ Materias disponibles para cursar: {len(disponibles)}")
    print(f"🔒 Materias que requieren prerrequisitos: {len(bloqueadas)}")
    
    if disponibles:
        print(f"\n🎯 MATERIAS DISPONIBLES PARA ESTE SEMESTRE:")
        print("-" * 60)
        for i, codigo in enumerate(sorted(disponibles), 1):
            nombre = materias_info[codigo]['nombre']
            print(f"{i:2d}. {codigo}: {nombre}")
    
    if bloqueadas:
        print(f"\n🔒 MATERIAS BLOQUEADAS (ejemplos):")
        print("-" * 60)
        for i, codigo in enumerate(sorted(bloqueadas)[:10], 1):
            info = materias_info[codigo]
            nombre = info['nombre']
            prereqs_pendientes = [p for p in info['prerrequisitos'] if p in materias_info]
            
            print(f"{i:2d}. {codigo}: {nombre}")
            if prereqs_pendientes:
                print(f"    📋 Requiere: {', '.join(prereqs_pendientes)}")

def mostrar_no_cursadas_con_grafico(ruta_no_cursadas):
    """Muestra las materias no cursadas y ofrece gráfico mejorado"""
    try:
        print("\n📚 MATERIAS PENDIENTES:")
        print("=" * 70)
        
        contador = 0
        with open(ruta_no_cursadas, 'r', encoding='utf-8') as f:
            for linea in f:
                linea = linea.strip()
                if linea:
                    partes = linea.split(':')
                    if len(partes) >= 3:
                        codigo = partes[0].strip()
                        nombre = partes[1].strip()
                        prereqs = partes[2].strip()
                        
                        print(f"{contador+1:2d}. {codigo}: {nombre}")
                        if prereqs:
                            print(f"    📋 Prerrequisitos: {prereqs}")
                        else:
                            print(f"    ✅ Sin prerrequisitos pendientes")
                        print()
                        contador += 1
        
        if contador == 0:
            print("❌ No se encontraron materias en el archivo.")
            return
        
        print(f"📊 Total: {contador} materias pendientes")
        print("\n" + "="*70)
        respuesta = input("¿Deseas ver el árbol jerárquico de dependencias? (s/n): ").strip().lower()
        
        if respuesta == 's':
            print("🔄 Generando gráfico interactivo con Graphviz...")
            graficar_materias_no_cursadas_graphviz(ruta_no_cursadas)
        
    except FileNotFoundError:
        print("❌ Archivo de materias no cursadas no encontrado.")
    except Exception as e:
        print(f"❌ Error al procesar el archivo: {e}")

def mostrar_dependientes_directos(codigo):
    nodo = grafo_materias.obtener_nodo(codigo)
    if nodo:
        if nodo.hijos:
            print(f"\nDependientes directos de {codigo} - {materias.get(codigo, '')}:")
            for hijo in nodo.hijos:
                print(f"- {hijo}: {materias.get(hijo, 'Materia no encontrada')}")
        else:
            print("Esta materia no tiene dependientes directos.")
    else:
        print("Materia no encontrada.")

def mostrar_dependientes_jerarquico(codigo):
    """Muestra dependientes con jerarquía"""
    nodo = grafo_materias.obtener_nodo(codigo)
    if not nodo:
        print("Materia no encontrada.")
        return
    
    print(f"\nDependientes de {codigo} - {materias.get(codigo, '')}:")
    print("=" * 60)
    
    dependientes = obtener_dependientes_indirectos(codigo)
    
    if not dependientes:
        print("Esta materia no tiene dependientes.")
        return
    
    niveles = {codigo: 0}
    cola = deque([(codigo, 0)])
    
    while cola:
        nodo_actual, nivel_actual = cola.popleft()
        nodo_obj = grafo_materias.obtener_nodo(nodo_actual)
        
        for hijo in nodo_obj.hijos:
            nivel_hijo = nivel_actual + 1
            if hijo not in niveles or nivel_hijo > niveles[hijo]:
                niveles[hijo] = nivel_hijo
                cola.append((hijo, nivel_hijo))
    
    nodos_por_nivel = defaultdict(list)
    for nodo, nivel in niveles.items():
        if nodo != codigo:
            nodos_por_nivel[nivel].append(nodo)
    
    for nivel in sorted(nodos_por_nivel.keys()):
        if nivel == 1:
            print("📚 DEPENDIENTES DIRECTOS:")
        else:
            print(f"📚 NIVEL {nivel} (Dependientes indirectos):")
        
        for nodo in sorted(nodos_por_nivel[nivel]):
            indentacion = "  " * (nivel - 1)
            print(f"{indentacion}• {nodo}: {materias.get(nodo, 'Materia no encontrada')}")
        print()
    
    total_dependientes = sum(len(nodos) for nodos in nodos_por_nivel.values())
    print(f"📊 Total de dependientes: {total_dependientes}")

# Menú principal
def menu():
    while True:
        print("\n" + "="*70)
        print("📚 SISTEMA DE GESTIÓN DE PENSUM")
        print("="*70)
        print("1. Ver pensum completo")
        print("2. Consultar prerrequisitos de materia por código")
        print("3. Consultar todos los prerrequisitos directos e indirectos")
        print("4. Ver dependientes de una materia")
        print("5. Ver dependientes directos e indirectos")
        print("6. Asignaturas sin cursar")
        print("7. Limpiar consola")
        print("8. Salir")
        print("="*70)
        opcion = input("Seleccione una opción: ")

        if opcion == "1":
            mostrar_pensum()
        elif opcion == "2":
            codigo = input("Ingrese el código de la materia: ").strip().upper()
            if codigo in materias:
                print(f"{codigo}: {materias[codigo]}")
                mostrar_prerrequisitos(codigo)
            else:
                print("Materia no encontrada.")
        elif opcion == "3":
            codigo = input("Ingrese el código de la materia: ").strip().upper()
            prerrequisitos = obtener_prerrequisitos_indirectos(codigo)
            if prerrequisitos:
                print(f"Todos los prerrequisitos de {codigo}: {', '.join(prerrequisitos)}")
                ver_grafico = input("¿Deseas ver un gráfico interactivo? (s/n): ").strip().lower()
                if ver_grafico == 's':
                    graficar_prerrequisitos_graphviz(codigo)
            else:
                print("No tiene prerrequisitos indirectos.")
        elif opcion == "4":
            codigo = input("Ingrese el código de la materia: ").strip().upper()
            mostrar_dependientes_directos(codigo)
        elif opcion == "5":
            codigo = input("Ingrese el código de la materia: ").strip().upper()
            nodo = grafo_materias.obtener_nodo(codigo)
            if nodo:
                mostrar_dependientes_jerarquico(codigo)
                ver_grafico = input("¿Deseas ver un gráfico interactivo? (s/n): ").strip().lower()
                if ver_grafico == 's':
                    graficar_dependientes_graphviz(codigo)
            else:
                print("Materia no encontrada.")
        elif opcion == "6":
            ruta_no_cursadas = r"sin_cursar.txt"
            mostrar_no_cursadas_con_grafico(ruta_no_cursadas)
        elif opcion == "7":
            limpiar_consola()
        elif opcion == "8":
            print("👋 Saliendo del programa. ¡Hasta pronto!")
            break
        else:
            print("❌ Opción inválida.")

# Cargar el archivo y ejecutar el menú
if __name__ == "__main__":
    ruta_archivo = r"pensum.txt"
    print("🔄 Cargando pensum...")
    leer_archivo(ruta_archivo)
    print("✅ Pensum cargado correctamente")
    menu()