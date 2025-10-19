import os
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict, deque

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
                    if pr:  # Solo si no está vacío
                        grafo_materias.agregar_arista(pr, codigo_materia)

    except FileNotFoundError:
        print("Archivo no encontrado. Asegúrate de que la ruta es correcta.")
    except Exception as e:
        print(f"Ocurrió un error al leer el archivo: {e}")

# Función para limpiar la consola
def limpiar_consola():
    os.system('cls' if os.name == 'nt' else 'clear')

# Función para mostrar el pensum completo
def mostrar_pensum():
    if materias:
        print("\nPensum completo:")
        for codigo, nombre in materias.items():
            print(f"{codigo}: {nombre}")
    else:
        print("El pensum no ha sido cargado correctamente.")

# Función para mostrar los prerrequisitos de una materia
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


def graficar_prerrequisitos(materia):
    nodo = grafo_materias.obtener_nodo(materia)
    if not nodo:
        print("Materia no encontrada.")
        return
    
    # Obtener todos los prerrequisitos indirectos
    prerrequisitos = obtener_prerrequisitos_indirectos(materia)
    
    if not prerrequisitos:
        print(f"La materia {materia} no tiene prerrequisitos para graficar.")
        return
    
    G = nx.DiGraph()
    visitados = set()

    def agregar_conexiones_reales(nodo_actual):
        """Agrega solo las conexiones directas reales del grafo"""
        if nodo_actual.valor in visitados:
            return
        visitados.add(nodo_actual.valor)
        
        # Agregar conexiones directas (padres -> nodo_actual)
        for padre in nodo_actual.padres:
            G.add_edge(padre, nodo_actual.valor)
            # Recursivamente agregar las conexiones de los padres
            padre_nodo = grafo_materias.obtener_nodo(padre)
            if padre_nodo:
                agregar_conexiones_reales(padre_nodo)

    # Construir el grafo con conexiones reales
    agregar_conexiones_reales(nodo)

    if not G.nodes:
        print("No hay prerrequisitos para graficar.")
        return

    # Crear etiquetas más compactas
    labels = {}
    for codigo in G.nodes:
            labels[codigo] = codigo

    # Configurar la visualización
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Dibujar el grafo
    nx.draw(G, pos, labels=labels, with_labels=True, 
            node_color='lightgreen', node_size=3000, 
            font_size=8, arrows=True, arrowsize=20,
            edge_color='gray', linewidths=2)
    
    plt.title(f"Prerrequisitos de {materia} - {materias.get(materia, '')}", fontsize=14)
    plt.tight_layout()
    plt.show()


# Función CORREGIDA para graficar dependientes
def graficar_dependientes(materia):
    nodo = grafo_materias.obtener_nodo(materia)
    if not nodo:
        print("Materia no encontrada.")
        return

    G = nx.DiGraph()
    visitados = set()

    def agregar_conexiones_dependientes(nodo_actual):
        """Agrega solo las conexiones directas reales del grafo para dependientes"""
        if nodo_actual.valor in visitados:
            return
        visitados.add(nodo_actual.valor)
        
        # Agregar conexiones directas (nodo_actual -> hijos)
        for hijo in nodo_actual.hijos:
            G.add_edge(nodo_actual.valor, hijo)
            # Recursivamente agregar las conexiones de los hijos
            hijo_nodo = grafo_materias.obtener_nodo(hijo)
            if hijo_nodo:
                agregar_conexiones_dependientes(hijo_nodo)

    # Construir el grafo con conexiones reales
    agregar_conexiones_dependientes(nodo)

    if not G.nodes:
        print("Esta materia no tiene dependientes para graficar.")
        return

    # Crear etiquetas SOLO con códigos (SIN NOMBRES)
    labels = {}
    for codigo in G.nodes:
        labels[codigo] = codigo

    # Configurar la visualización
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Dibujar el grafo
    nx.draw(G, pos, labels=labels, with_labels=True, 
            node_color='lightcoral', node_size=3000, 
            font_size=10, arrows=True, arrowsize=20,
            edge_color='gray', linewidths=2)
    
    plt.title(f"Dependientes de {materia} - {materias.get(materia, '')}", fontsize=14)
    plt.tight_layout()
    plt.show()

# Función CORREGIDA para obtener todos los dependientes sin repetir
def obtener_dependientes_indirectos(materia):
    """Obtiene todos los dependientes directos e indirectos de una materia sin repetir"""
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

def graficar_materias_no_cursadas(ruta_no_cursadas):
    """Grafica las materias no cursadas con layout jerárquico correcto"""
    try:
        # Leer las materias no cursadas CON SUS PRERREQUISITOS
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
                        
                        # Procesar prerrequisitos
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
        
        # Crear el grafo dirigido solo con materias no cursadas
        G = nx.DiGraph()
        
        # Agregar nodos
        for codigo in materias_no_cursadas:
            G.add_node(codigo)
        
        # Agregar aristas solo entre materias no cursadas
        materias_disponibles = []
        materias_bloqueadas = []
        
        for codigo, info in materias_no_cursadas.items():
            prereqs_pendientes = []
            
            # Solo considerar prerrequisitos que están en materias no cursadas
            for prereq in info['prerrequisitos']:
                if prereq in materias_no_cursadas:
                    prereqs_pendientes.append(prereq)
                    G.add_edge(prereq, codigo)
            
            # Si no tiene prerrequisitos pendientes, está disponible
            if not prereqs_pendientes:
                materias_disponibles.append(codigo)
            else:
                materias_bloqueadas.append(codigo)
        
        print(f"Materias disponibles: {len(materias_disponibles)}")
        print(f"Materias bloqueadas: {len(materias_bloqueadas)}")
        
        # Crear layout jerárquico CORRECTO
        pos = crear_layout_jerarquico_correcto(G, materias_disponibles)
        
        # Configurar figura más grande
        plt.figure(figsize=(16, 12))
        
        # Crear etiquetas solo con códigos
        labels = {}
        for codigo in G.nodes:
            labels[codigo] = codigo
        
        # Dibujar nodos con diferentes colores
        if materias_disponibles:
            nx.draw_networkx_nodes(G, pos, nodelist=materias_disponibles, 
                                  node_color='lightgreen', node_size=2000, 
                                  alpha=0.8, edgecolors='darkgreen', linewidths=2)
        
        if materias_bloqueadas:
            nx.draw_networkx_nodes(G, pos, nodelist=materias_bloqueadas, 
                                  node_color='lightcoral', node_size=2000, 
                                  alpha=0.8, edgecolors='darkred', linewidths=2)
        
        # Dibujar aristas
        if G.edges:
            nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, 
                                  arrowsize=20, arrowstyle='->', width=2, alpha=0.7)
        
        # Dibujar etiquetas
        nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')
        
        plt.title("Árbol de Materias No Cursadas\n(Verde: Listas para cursar | Rojo: Requieren prerrequisitos)", 
                 fontsize=16, fontweight='bold', pad=20)
        
        # Leyenda mejorada
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='lightgreen', 
                   markeredgecolor='darkgreen', markersize=15, 
                   label=f'Disponibles ({len(materias_disponibles)})'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='lightcoral', 
                   markeredgecolor='darkred', markersize=15, 
                   label=f'Bloqueadas ({len(materias_bloqueadas)})')
        ]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=12)
        
        plt.axis('off')
        plt.tight_layout()
        plt.show()
        
        # Mostrar análisis detallado
        mostrar_analisis_detallado(materias_disponibles, materias_bloqueadas, materias_no_cursadas)
        
    except FileNotFoundError:
        print("❌ Archivo de materias no cursadas no encontrado.")
    except Exception as e:
        print(f"❌ Error al crear el gráfico: {e}")
        import traceback
        traceback.print_exc()

def crear_layout_jerarquico_correcto(G, materias_disponibles):
    """Crea un layout jerárquico donde las materias prereq están arriba de sus dependientes"""
    
    # Calcular niveles usando ordenamiento topológico
    niveles = {}
    
    # Nivel 0: materias sin prerrequisitos (disponibles)
    for materia in materias_disponibles:
        niveles[materia] = 0
    
    # Usar BFS para asignar niveles
    cola = deque([(materia, 0) for materia in materias_disponibles])
    
    while cola:
        nodo_actual, nivel_actual = cola.popleft()
        
        # Para cada materia que depende de la actual
        for sucesor in G.successors(nodo_actual):
            # El nivel del sucesor debe ser al menos nivel_actual + 1
            nivel_sucesor = nivel_actual + 1
            
            # Si ya tiene un nivel asignado, tomar el máximo
            if sucesor in niveles:
                nivel_sucesor = max(niveles[sucesor], nivel_sucesor)
            
            # Solo actualizar si es un nivel mayor
            if sucesor not in niveles or nivel_sucesor > niveles[sucesor]:
                niveles[sucesor] = nivel_sucesor
                cola.append((sucesor, nivel_sucesor))
    
    # Asegurar que todos los nodos tengan nivel
    for nodo in G.nodes:
        if nodo not in niveles:
            # Calcular nivel basado en prerrequisitos
            predecesores = list(G.predecessors(nodo))
            if predecesores:
                nivel_max = max([niveles.get(pred, 0) for pred in predecesores])
                niveles[nodo] = nivel_max + 1
            else:
                niveles[nodo] = 0
    
    # Organizar nodos por nivel
    nodos_por_nivel = defaultdict(list)
    for nodo, nivel in niveles.items():
        nodos_por_nivel[nivel].append(nodo)
    
    # Asignar posiciones
    pos = {}
    espaciado_vertical = 9
    espaciado_horizontal = 8
    
    for nivel in sorted(nodos_por_nivel.keys()):
        nodos = nodos_por_nivel[nivel]
        y = -nivel * espaciado_vertical  # Niveles más altos van arriba
        
        # Distribuir horizontalmente
        if len(nodos) == 1:
            pos[nodos[0]] = (0, y)
        else:
            ancho_total = (len(nodos) - 1) * espaciado_horizontal
            x_inicio = -ancho_total / 2
            
            for i, nodo in enumerate(nodos):
                x = x_inicio + i * espaciado_horizontal
                pos[nodo] = (x, y)
    
    return pos


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
            
            # Mostrar prerrequisitos pendientes
            prereqs_pendientes = []
            for prereq in info['prerrequisitos']:
                if prereq in materias_info:
                    prereqs_pendientes.append(prereq)
            
            print(f"{i:2d}. {codigo}: {nombre}")
            if prereqs_pendientes:
                print(f"    📋 Requiere: {', '.join(prereqs_pendientes)}")
    
    print(f"\n💡 RECOMENDACIONES:")
    print("   • Enfócate en las materias VERDES del gráfico")
    print("   • Cada materia verde completada desbloqueará otras rojas")
    print("   • Planifica tu carga académica considerando la dificultad")


# Función mejorada para mostrar materias no cursadas
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
        
        # Ofrecer visualización gráfica
        print("\n" + "="*70)
        respuesta = input("¿Deseas ver el árbol jerárquico de dependencias? (s/n): ").strip().lower()
        
        if respuesta == 's':
            print("🔄 Generando gráfico jerárquico...")
            graficar_materias_no_cursadas(ruta_no_cursadas)
        
    except FileNotFoundError:
        print("❌ Archivo de materias no cursadas no encontrado.")
        print("📁 Verifica la ruta del archivo.")
    except Exception as e:
        print(f"❌ Error al procesar el archivo: {e}")


# Función auxiliar para verificar prerrequisitos
def verificar_prerrequisitos_pendientes(materia, materias_no_cursadas):
    """Verifica qué prerrequisitos de una materia aún no se han cursado"""
    nodo = grafo_materias.obtener_nodo(materia)
    if not nodo:
        return []
    
    prerrequisitos_pendientes = []
    for padre in nodo.padres:
        if padre in materias_no_cursadas:
            prerrequisitos_pendientes.append(padre)
    
    return prerrequisitos_pendientes

# Función modificada para mostrar materias no cursadas
def mostrar_no_cursadas_con_grafico(ruta_no_cursadas):
    """Muestra las materias no cursadas y ofrece opción de graficar"""
    try:
        materias_mostradas = []
        with open(ruta_no_cursadas, 'r', encoding='utf-8') as f:
            print("\nMaterias que no has cursado:")
            print("-" * 50)
            contador = 0
            for linea in f:
                linea = linea.strip()
                if linea:
                    partes = linea.split(':')
                    if len(partes) >= 2:
                        codigo = partes[0].strip()
                        nombre = partes[1].strip()
                        print(f"{contador+1:2d}. {codigo}: {nombre}")
                        materias_mostradas.append(codigo)
                        contador += 1
                    else:
                        print(f"{contador+1:2d}. {linea}")
                        contador += 1
            
            if contador == 0:
                print("El archivo está vacío o no contiene materias válidas.")
                return
            else:
                print(f"\nTotal: {contador} materias no cursadas")
                
                # Preguntar si quiere ver el gráfico
                print("\n" + "="*50)
                ver_grafico = input("¿Deseas ver el árbol gráfico de las materias? (s/n): ").strip().lower()
                if ver_grafico == 's':
                    print("Generando gráfico... (puede tomar unos segundos)")
                    graficar_materias_no_cursadas(ruta_no_cursadas)
                
    except FileNotFoundError:
        print("❌ Archivo de materias no cursadas no encontrado.")
        print("Verifica que el archivo existe en la ruta especificada.")
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")


# Función corregida para obtener prerrequisitos directos e indirectos
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
    """Muestra dependientes con jerarquía y sin repeticiones"""
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
    
    # Organizar por niveles
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
    
    # Mostrar por niveles
    nodos_por_nivel = defaultdict(list)
    for nodo, nivel in niveles.items():
        if nodo != codigo:  # Excluir el nodo raíz
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
    
    # Mostrar resumen
    total_dependientes = sum(len(nodos) for nodos in nodos_por_nivel.values())
    print(f"📊 Total de dependientes: {total_dependientes}")



# Menú principal
def menu():
    while True:
        print("\nMenú:")
        print("1. Ver pensum completo")
        print("2. Consultar prerrequisitos de materia por código")
        print("3. Consultar todos los prerrequisitos directos e indirectos")
        print("4. Ver dependientes de una materia")
        print("5. Ver dependientes directos e indirectos")
        print("6. Asignaturas sin cursar")
        print("7. Limpiar consola")
        print("8. Salir")
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
                ver_grafico = input("¿Deseas ver un gráfico de los prerrequisitos? (s/n): ").strip().lower()
                if ver_grafico == 's':
                    graficar_prerrequisitos(codigo)
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
                ver_grafico = input("¿Deseamostrar_dependientes_jerarquicos ver un gráfico de los dependientes? (s/n): ").strip().lower()
                if ver_grafico == 's':
                    graficar_dependientes(codigo)
            else:
                print("Materia no encontrada.")

                #
        elif opcion == "6":
            ruta_no_cursadas = r"sin_cursar.txt" #asignaturas sin cursar
            #ruta_no_cursadas = r"C:\Users\Dell\OneDrive\Escritorio\Python\pensum.txt" #pensum completo

            mostrar_no_cursadas_con_grafico(ruta_no_cursadas)
        elif opcion == "7":
            limpiar_consola()
        elif opcion == "8":
            print("Saliendo del programa.")
            break
        else:
            print("Opción inválida.")

# Cargar el archivo y ejecutar el menú
ruta_archivo = r"pensum.txt"  
leer_archivo(ruta_archivo)
menu()