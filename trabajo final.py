import os
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

def generar_html_con_tooltips(svg_content, tooltips_map, output_file):
    """Genera un archivo HTML con el SVG y tooltips interactivos"""
    
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pensum Interactivo</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 95%;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            padding: 30px;
        }}
        
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2em;
        }}
        
        #svg-container {{
            width: 100%;
            overflow: auto;
            border: 2px solid #ddd;
            border-radius: 10px;
            background: #fafafa;
            padding: 20px;
        }}
        
        svg {{
            max-width: 100%;
            height: auto;
        }}
        
        .tooltip {{
            position: fixed;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            pointer-events: none;
            z-index: 1000;
            display: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            max-width: 300px;
        }}
        
        .tooltip.show {{
            display: block;
        }}
        
        .tooltip strong {{
            display: block;
            margin-bottom: 5px;
            font-size: 16px;
            color: #4CAF50;
        }}
        
        .node {{
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .node:hover ellipse,
        .node:hover polygon {{
            fill: #FFD54F !important;
            stroke: #F57C00 !important;
            stroke-width: 3 !important;
        }}
        
        .instructions {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #2196F3;
        }}
        
        .instructions p {{
            margin: 5px 0;
            color: #1565C0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Visualizador de Pensum Interactivo</h1>
        
        <div class="instructions">
            <p><strong>💡 Instrucciones:</strong></p>
            <p>• Pasa el cursor sobre cualquier materia para ver su nombre completo</p>
            <p>• Las flechas muestran las dependencias entre materias</p>
            <p>• Puedes hacer zoom con Ctrl+Scroll o el trackpad</p>
        </div>
        
        <div id="svg-container">
            {svg_content}
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        const tooltips = {tooltips_map};
        const tooltip = document.getElementById('tooltip');
        const nodes = document.querySelectorAll('.node');
        
        nodes.forEach(node => {{
            const title = node.querySelector('title');
            if (title) {{
                const codigo = title.textContent.trim();
                
                node.addEventListener('mouseenter', (e) => {{
                    if (tooltips[codigo]) {{
                        tooltip.innerHTML = `<strong>${{codigo}}</strong>${{tooltips[codigo]}}`;
                        tooltip.classList.add('show');
                    }}
                }});
                
                node.addEventListener('mousemove', (e) => {{
                    tooltip.style.left = (e.clientX + 15) + 'px';
                    tooltip.style.top = (e.clientY + 15) + 'px';
                }});
                
                node.addEventListener('mouseleave', () => {{
                    tooltip.classList.remove('show');
                }});
            }}
        }});
    </script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)

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
             fontname='Arial', fontsize='10')
    dot.attr('edge', color='#555555', penwidth='2', arrowsize='1')
    dot.attr(splines='line')  # Líneas rectas
    dot.attr(bgcolor='#f9f9f9')
    
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
    dot.node(materia, materia, fillcolor='#FFD54F', color='#F57C00', penwidth='3')
    
    # Generar SVG
    output_name = f'prerrequisitos_{materia}'
    dot.render(output_name, format='svg', cleanup=True)
    
    # Leer SVG y crear HTML con tooltips
    with open(f'{output_name}.svg', 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    html_file = f'{output_name}.html'
    generar_html_con_tooltips(svg_content, str(tooltips), html_file)
    
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
             fontname='Arial', fontsize='10')
    dot.attr('edge', color='#555555', penwidth='2', arrowsize='1')
    dot.attr(splines='line')  # Líneas rectas
    dot.attr(bgcolor='#f9f9f9')
    
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
    dot.node(materia, materia, fillcolor='#FF6B6B', color='#C92A2A', penwidth='3')
    
    # Generar SVG y HTML
    output_name = f'dependientes_{materia}'
    dot.render(output_name, format='svg', cleanup=True)
    
    with open(f'{output_name}.svg', 'r', encoding='utf-8') as f:
        svg_content = f.read()
    
    html_file = f'{output_name}.html'
    generar_html_con_tooltips(svg_content, str(tooltips), html_file)
    
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
        dot.attr('node', shape='box', style='filled,rounded', fontname='Arial', fontsize='10')
        dot.attr('edge', color='#555555', penwidth='2', arrowsize='1')
        dot.attr(splines='line')  # Líneas rectas
        dot.attr(bgcolor='#f9f9f9')
        
        materias_disponibles = []
        materias_bloqueadas = []
        tooltips = {}
        
        # Clasificar materias
        for codigo, info in materias_no_cursadas.items():
            prereqs_pendientes = [p for p in info['prerrequisitos'] if p in materias_no_cursadas]
            tooltips[codigo] = info['nombre']
            
            if not prereqs_pendientes:
                materias_disponibles.append(codigo)
                dot.node(codigo, codigo, fillcolor='lightgreen', color='darkgreen', penwidth='2')
            else:
                materias_bloqueadas.append(codigo)
                dot.node(codigo, codigo, fillcolor='lightcoral', color='darkred', penwidth='2')
        
        # Agregar aristas
        for codigo, info in materias_no_cursadas.items():
            for prereq in info['prerrequisitos']:
                if prereq in materias_no_cursadas:
                    dot.edge(prereq, codigo)
        
        print(f"✅ Materias disponibles: {len(materias_disponibles)}")
        print(f"🔒 Materias bloqueadas: {len(materias_bloqueadas)}")
        
        # Generar SVG y HTML
        output_name = 'materias_no_cursadas'
        dot.render(output_name, format='svg', cleanup=True)
        
        with open(f'{output_name}.svg', 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        html_file = f'{output_name}.html'
        generar_html_con_tooltips(svg_content, str(tooltips), html_file)
        
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