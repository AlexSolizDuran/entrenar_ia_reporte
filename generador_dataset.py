import pandas as pd
import json
import random

# --- 1. Plantillas de SQL (Actualizadas con todas las categorías) ---
# He añadido docenas de nuevas plantillas
TEMPLATES = [
    # --- GANANCIAS (PROFIT) ---
    (
        "¿Cuál fue la ganancia total?",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_total FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id;"
    ),
    (
        "Ganancias de hoy",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_total FROM detalle_venta dv JOIN venta v ON dv.venta_id = v.id JOIN prod_variante pv ON dv.prod_variante_id = pv.id WHERE DATE(v.fecha_venta) = DATE('now');"
    ),
    (
        "rentabilidad del producto {producto}",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_producto FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id WHERE p.descripcion = '{producto}';"
    ),
    (
        "ganancias de la categoría {categoria}",
        "SELECT SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_categoria FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN categoria c ON p.categoria_id = c.id WHERE c.nombre = '{categoria}';"
    ),
    (
        "Ganancias por marca",
        "SELECT b.nombre, SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_marca FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id GROUP BY b.nombre ORDER BY ganancia_marca DESC;"
    ),
    (
        "Producto más rentable",
        "SELECT p.descripcion, SUM(dv.subtotal - (pv.costo * dv.cantidad)) AS ganancia_producto FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id GROUP BY p.descripcion ORDER BY ganancia_producto DESC LIMIT 1;"
    ),

    # --- VENTAS (REVENUE) ---
    (
        "Total vendido",
        "SELECT SUM(monto_total) AS ventas_totales FROM venta;"
    ),
    (
        "ventas de ayer",
        "SELECT SUM(monto_total) AS ventas_ayer FROM venta WHERE DATE(fecha_venta) = DATE('now', '-1 day');"
    ),
    (
        "ventas de esta semana",
        "SELECT SUM(monto_total) AS ventas_semana FROM venta WHERE DATE(fecha_venta) >= DATE('now', 'weekday 0', '-6 days');"
    ),
    (
        "Ventas del vendedor {vendedor_username}",
        "SELECT SUM(v.monto_total) FROM venta v JOIN usuario u ON v.vendedor_id = u.id WHERE u.username = '{vendedor_username}';"
    ),
    (
        "Ventas del producto {producto}",
        "SELECT SUM(dv.subtotal) AS ventas_producto FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id WHERE p.descripcion = '{producto}';"
    ),
    (
        "Ventas de la marca {marca}",
        "SELECT SUM(dv.subtotal) AS total_ventas FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id WHERE b.nombre = '{marca}';"
    ),
    (
        "Ventas por categoría",
        "SELECT c.nombre, SUM(dv.subtotal) AS total_ventas FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN categoria c ON p.categoria_id = c.id GROUP BY c.nombre ORDER BY total_ventas DESC;"
    ),
    (
        "Ventas por marca",
        "SELECT b.nombre, SUM(dv.subtotal) AS total_ventas FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id GROUP BY b.nombre ORDER BY total_ventas DESC;"
    ),
    (
        "Ventas de productos de {material}",
        "SELECT SUM(dv.subtotal) FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN material m ON p.material_id = m.id WHERE m.nombre = '{material}';"
    ),
    (
        "Ventas de productos con la etiqueta {etiqueta}",
        "SELECT SUM(dv.subtotal) FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN producto_etiqueta pe ON p.id = pe.producto_id JOIN etiqueta e ON pe.etiqueta_id = e.id WHERE e.nombre = '{etiqueta}';"
    ),

    # --- PRODUCTOS MÁS VENDIDOS (UNIDADES) ---
    (
        "Producto más vendido",
        "SELECT p.descripcion, SUM(dv.cantidad) AS total_vendido FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id GROUP BY p.descripcion ORDER BY total_vendido DESC LIMIT 1;"
    ),
    (
        "Top 5 productos más vendidos",
        "SELECT p.descripcion, SUM(dv.cantidad) AS total_vendido FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id GROUP BY p.descripcion ORDER BY total_vendido DESC LIMIT 5;"
    ),
    (
        "Producto menos vendido",
        "SELECT p.descripcion, SUM(dv.cantidad) AS total_vendido FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id GROUP BY p.descripcion ORDER BY total_vendido ASC LIMIT 1;"
    ),
    (
        "Unidades vendidas de {producto}",
        "SELECT SUM(dv.cantidad) AS unidades_vendidas FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id WHERE p.descripcion = '{producto}';"
    ),
    (
        "Categoría más vendida",
        "SELECT c.nombre, SUM(dv.cantidad) AS total_unidades FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN categoria c ON p.categoria_id = c.id GROUP BY c.nombre ORDER BY total_unidades DESC LIMIT 1;"
    ),
    (
        "Ventas de productos talla {talla}",
        "SELECT SUM(dv.cantidad) FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN talla t ON pv.id_talla = t.id WHERE t.talla = '{talla}';"
    ),
    (
        "Cuántas unidades vendimos de color {color}",
        "SELECT SUM(dv.cantidad) FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN color c ON pv.id_color = c.id WHERE c.nombre = '{color}';"
    ),
    (
        "Producto más vendido de color {color}",
        "SELECT p.descripcion, SUM(dv.cantidad) AS total FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN color c ON pv.id_color = c.id WHERE c.nombre = '{color}' GROUP BY p.descripcion ORDER BY total DESC LIMIT 1;"
    ),

    # --- INVENTARIO Y STOCK ---
    (
        "Stock del SKU {sku}",
        "SELECT stock FROM prod_variante WHERE sku = '{sku}';"
    ),
    (
        "Stock total del producto {producto}",
        "SELECT SUM(pv.stock) AS stock_total FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id WHERE p.descripcion = '{producto}';"
    ),
    (
        "Inventario del producto {producto}",
        "SELECT t.talla, c.nombre AS color, pv.stock FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id JOIN talla t ON pv.id_talla = t.id JOIN color c ON pv.id_color = c.id WHERE p.descripcion = '{producto}' ORDER BY t.talla, c.nombre;"
    ),
    (
        "Productos con bajo stock (menos de 10 unidades)",
        "SELECT p.descripcion, pv.sku, pv.stock FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id WHERE pv.stock < 10 ORDER BY pv.stock ASC;"
    ),
    (
        "Costo total del inventario",
        "SELECT SUM(pv.costo * pv.stock) AS costo_inventario_total FROM prod_variante pv;"
    ),
    (
        "Stock de productos de color {color}",
        "SELECT SUM(pv.stock) FROM prod_variante pv JOIN color c ON pv.id_color = c.id WHERE c.nombre = '{color}';"
    ),
    (
        "Cuántos productos en talla {talla} tenemos en stock",
        "SELECT SUM(pv.stock) FROM prod_variante pv JOIN talla t ON pv.id_talla = t.id WHERE t.talla = '{talla}';"
    ),
    (
        "Stock total de la categoría {categoria}",
        "SELECT SUM(pv.stock) FROM prod_variante pv JOIN producto p ON pv.id_producto = p.id JOIN categoria c ON p.categoria_id = c.id WHERE c.nombre = '{categoria}';"
    ),

    # --- CONTEOS Y LISTAS ---
    (
        "Total de clientes registrados",
        "SELECT COUNT(u.id) FROM usuario u JOIN rol r ON u.rol_id = r.id WHERE r.nombre = 'CLIENTE';"
    ),
    (
        "Total de productos con la etiqueta {etiqueta}",
        "SELECT COUNT(p.id) FROM producto p JOIN producto_etiqueta pe ON p.id = pe.producto_id JOIN etiqueta e ON pe.etiqueta_id = e.id WHERE e.nombre = '{etiqueta}';"
    ),
    (
        "Lista de productos {etiqueta}",
        "SELECT p.descripcion FROM producto p JOIN producto_etiqueta pe ON p.id = pe.producto_id JOIN etiqueta e ON pe.etiqueta_id = e.id WHERE e.nombre = '{etiqueta}';"
    ),
    (
        "Cuántos productos de la marca {marca} hay",
        "SELECT COUNT(p.id) FROM producto p JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id WHERE b.nombre = '{marca}';"
    ),
    (
        "Lista de productos {marca}",
        "SELECT p.descripcion FROM producto p JOIN modelo m ON p.modelo_id = m.id JOIN marca b ON m.marca_id = b.id WHERE b.nombre = '{marca}';"
    ),
    (
        "Cuántos productos son de {material}",
        "SELECT COUNT(p.id) FROM producto p JOIN material m ON p.material_id = m.id WHERE m.nombre = '{material}';"
    ),
    (
        "Cuántos productos hay en la categoría {categoria}",
        "SELECT COUNT(p.id) FROM producto p JOIN categoria c ON p.categoria_id = c.id WHERE c.nombre = '{categoria}';"
    ),
    (
        "Ventas del modelo {modelo}",
        "SELECT SUM(dv.subtotal) FROM detalle_venta dv JOIN prod_variante pv ON dv.prod_variante_id = pv.id JOIN producto p ON pv.id_producto = p.id JOIN modelo m ON p.modelo_id = m.id WHERE m.nombre = '{modelo}';"
    )
]

# --- 2. Función para cargar los datos de tus CSVs (ACTUALIZADA) ---
def cargar_parametros():
    """Carga los datos de los CSVs en listas para usarlos en las plantillas."""
    try:
        # --- Lectura de CSVs ---
        # (Ajusta los 'sep' y 'header' si son diferentes)
        
        # Leídos anteriormente
        df_productos = pd.read_csv("./data_csvs/productos_data.csv", sep=';', header=None)
        df_categorias = pd.read_csv("./data_csvs/categorias_data.csv", sep=',', header=None)
        df_usuarios = pd.read_csv("./data_csvs/usuarios_data.csv", sep=',', header=None)
        df_variantes = pd.read_csv("./data_csvs/prod_variantes_data.csv", sep=';', header=None)
        df_etiquetas = pd.read_csv("./data_csvs/etiquetas_data.csv", sep=',', header=None)
        
        # --- NUEVOS CSVs ---
        df_marcas = pd.read_csv("./data_csvs/marcas_data.csv", sep=',', header=None)
        df_modelos = pd.read_csv("./data_csvs/modelos_data.csv", sep=',', header=None)
        df_materiales = pd.read_csv("./data_csvs/materiales_data.csv", sep=',', header=None)
        df_tallas = pd.read_csv("./data_csvs/tallas_data.csv", sep=',', header=None)
        df_colores = pd.read_csv("./data_csvs/colores_data.csv", sep=',', header=None)

        # --- Creación de Listas ---
        parametros = {
            "producto": df_productos[0].dropna().tolist(),
            "categoria": df_categorias[0].dropna().tolist(),
            "vendedor_username": df_usuarios[df_usuarios[6] == 'VENDEDOR'][0].dropna().tolist(),
            "sku": df_variantes[6].dropna().tolist(),
            "etiqueta": df_etiquetas[0].dropna().tolist(),
            
            # --- NUEVAS LISTAS ---
            "marca": df_marcas[0].dropna().tolist(),
            "modelo": df_modelos[0].dropna().tolist(),
            "material": df_materiales[0].dropna().tolist(),
            "talla": df_tallas[0].dropna().tolist(),
            "color": df_colores[0].dropna().tolist(),

            # --- Listas Estáticas ---
            "metodo_pago": ["Tarjeta", "Efectivo", "QR"],
            "estado_pedido": ["pendiente", "enviado", "entregado", "cancelado"]
        }
        
        # Filtrar listas vacías que causarían errores
        for key, val in parametros.items():
            if not val:
                print(f"Advertencia: No se encontraron datos para '{key}'. Esa plantilla se omitirá.")
        
        return parametros
        
    except FileNotFoundError as e:
        print(f"Error: No se encontró el archivo {e.filename}.")
        print("Asegúrate de haber creado la carpeta 'data_csvs' y copiado todos los .csv allí.")
        return None
    except Exception as e:
        print(f"Error cargando CSVs: {e}")
        return None

# --- 3. Script de Generación (ACTUALIZADO) ---

def generar_dataset(params, num_samples=500):
    """
    Genera un dataset de num_samples ejemplos.
    Ahora el prompt incluye el formato y la salida es un string JSON.
    """
    
    formatos = ["pdf", "excel", "json"] # JSON será nuestro default
    
    # Variaciones de cómo un usuario podría pedir un formato
    prompt_formatos = {
        "pdf": ["en pdf", "para un pdf", "genera un pdf de"],
        "excel": ["en excel", "para excel", "en un archivo excel", "genera un excel de"],
        "json": ["en json", "devuelve un json con", ""] # '' es para prompts sin formato
    }

    count = 0
    while count < num_samples:
        # 1. Elegir plantilla SQL y formato
        texto_base, sql_template = random.choice(TEMPLATES)
        formato_elegido = random.choice(formatos)
        
        # 2. Elegir una variación de prompt
        variacion_prompt = random.choice(prompt_formatos[formato_elegido])
        
        # 3. Crear el prompt final (texto de entrada)
        if variacion_prompt.startswith("genera un"):
            texto_final = f"genera un {formato_elegido} de {texto_base}"
        elif variacion_prompt:
            texto_final = f"{texto_base} {variacion_prompt}"
        else:
            texto_final = texto_base

        # 4. Añadir el prefijo de T5
        texto_final = "generar JSON: " + texto_final.lower()
        
        # 5. Llenar placeholders
        sql_final = sql_template
        
        # Variable para saltar si un placeholder no se puede llenar
        skip_plantilla = False
        
        # --- Reemplazo de Placeholders (ACTUALIZADO CON TODOS LOS NUEVOS) ---
        placeholders = {
            "{producto}": "producto",
            "{categoria}": "categoria",
            "{vendedor_username}": "vendedor_username",
            "{sku}": "sku",
            "{etiqueta}": "etiqueta",
            "{marca}": "marca",
            "{modelo}": "modelo",
            "{material}": "material",
            "{talla}": "talla",
            "{color}": "color",
            "{metodo_pago}": "metodo_pago",
            "{estado_pedido}": "estado_pedido"
        }

        for ph, key in placeholders.items():
            if ph in texto_final:
                if not params[key]: # Si la lista está vacía
                    skip_plantilla = True
                    break
                
                valor = random.choice(params[key])
                texto_final = texto_final.replace(ph, str(valor))
                sql_final = sql_final.replace(ph, str(valor).replace("'", "''")) # Escapar ' para SQL
        
        if skip_plantilla:
            continue # Salta esta iteración y prueba otra plantilla

        # 6. Crear el JSON de salida (¡como un string!)
        salida_dict = {
            "sql": sql_final,
            "formato": formato_elegido
        }
        salida_json_string = json.dumps(salida_dict) 

        # 7. Imprimir la línea del dataset
        linea_dataset = {"texto": texto_final, "salida_json": salida_json_string}
        print(json.dumps(linea_dataset, ensure_ascii=False))
        count += 1


if __name__ == "__main__":
    parametros = cargar_parametros()
    if parametros:
        # ¡Aumentemos el número de muestras!
        generar_dataset(parametros, num_samples=2000)