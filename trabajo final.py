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

# Plantilla HTML de los gráficos, junto a este script
RUTA_PLANTILLA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plantilla.html')


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


def generar_html_con_tooltips(svg_content, nombres, output_file, titulo='Pensum', resumen='', leyenda=None,
                              modo='pendientes'):
    """Genera un archivo HTML con el SVG, una leyenda y un panel de detalle por materia"""
    leyenda = leyenda or []
    svg_content = svg_content[svg_content.find('<svg'):]  # quitar el prólogo XML
    leyenda_html = ''.join(
        f'<li><span class="muestra muestra-{clase}"></span>{html.escape(texto)}</li>'
        for clase, texto in leyenda
    )

    with open(RUTA_PLANTILLA, 'r', encoding='utf-8') as f:
        plantilla = f.read()

    contenido = (plantilla
                 .replace('__TITULO__', html.escape(titulo))
                 .replace('__RESUMEN__', html.escape(resumen))
                 .replace('__LEYENDA__', leyenda_html)
                 .replace('__MODO__', modo)
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

def graficar_materias_no_cursadas_graphviz(ruta_no_cursadas, pensum_completo=False):
    """Grafica las materias no cursadas con Graphviz.
    Con pensum_completo=True grafica todo el pensum por trimestres, empezando en el 1"""
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
        output_name = ruta_grafico('pensum_completo' if pensum_completo else 'materias_no_cursadas')
        dot.render(output_name, format='svg', cleanup=True)
        
        with open(f'{output_name}.svg', 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        html_file = f'{output_name}.html'
        if pensum_completo:
            generar_html_con_tooltips(
                svg_content, tooltips, html_file,
                titulo='Pensum completo',
                resumen=f'El pensum tiene {len(materias_no_cursadas)} materias. Cada franja es un trimestre: '
                        f'arriba las {len(materias_disponibles)} que no tienen prerrequisitos y debajo lo que '
                        f'se abre al aprobarlas. La carrera dura como mínimo {max(niveles.values())} trimestres.',
                leyenda=[('disponible', 'Sin prerrequisitos, abre otras'),
                         ('no-abre', 'Sin prerrequisitos, no abre otras'),
                         ('bloqueada', 'Con prerrequisitos'), ('ruta', 'Prerrequisito de la materia que elijas')],
                modo='pensum',
            )
            webbrowser.open(f'file://{os.path.abspath(html_file)}')
            print(f"✅ Gráfico generado: {html_file}")
            return

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
            ver_grafico = input("¿Deseas ver el gráfico interactivo del pensum completo? (s/n): ").strip().lower()
            if ver_grafico == 's':
                print("🔄 Generando gráfico interactivo con Graphviz...")
                graficar_materias_no_cursadas_graphviz(r"pensum.txt", pensum_completo=True)
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