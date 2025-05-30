import cv2
import numpy as np

def get_color_point_coords(img, pts_rect, lower_hsv, upper_hsv, area_min=100):
    # 1. Ordenar puntos y calcular dimensiones del rectángulo destino
    pts = pts_rect.astype("float32")
    # Función auxiliar para ordenar (tl, tr, br, bl)
    def order_pts(pts):
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        tl = pts[np.argmin(s)]
        br = pts[np.argmax(s)]
        tr = pts[np.argmin(diff)]
        bl = pts[np.argmax(diff)]
        return np.array([tl, tr, br, bl], dtype="float32")

    rect = order_pts(pts)
    (tl, tr, br, bl) = rect
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxW = int(max(widthA, widthB))
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxH = int(max(heightA, heightB))

    # 2. Calcular matriz de transformación perspectiva
    dst = np.array([
        [0, 0],
        [maxW - 1, 0],
        [maxW - 1, maxH - 1],
        [0, maxH - 1]
    ], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)

    # 3. Convertir imagen a HSV y enmascarar color
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))

    # 4. Aplicar perspectiva al mask para llevarlo al sistema del rectángulo
    warped_mask = cv2.warpPerspective(mask, M, (maxW, maxH))

    # 5. Encontrar contornos y calcular centroide del más grande
    contornos, _ = cv2.findContours(warped_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mayor_area = 0
    mejor_cnt = None
    for cnt in contornos:
        area = cv2.contourArea(cnt)
        if area >= area_min and area > mayor_area:
            mayor_area = area
            mejor_cnt = cnt

    if mejor_cnt is None:
        return None

    Mmt = cv2.moments(mejor_cnt)
    if Mmt["m00"] == 0:
        return None
    cx = Mmt["m10"] / Mmt["m00"]
    cy = Mmt["m01"] / Mmt["m00"]

    return (cx, cy)


def order_points(pts):
    pts = pts.reshape(4, 2)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    ordered = np.zeros((4, 2), dtype="float32")
    ordered[0] = pts[np.argmin(s)]
    ordered[2] = pts[np.argmax(s)]
    ordered[1] = pts[np.argmin(diff)]
    ordered[3] = pts[np.argmax(diff)]
    return ordered

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxW = max(int(widthA), int(widthB))
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxH = max(int(heightA), int(heightB))
    dst = np.array([
        [0, 0],
        [maxW - 1, 0],
        [maxW - 1, maxH - 1],
        [0, maxH - 1]
    ], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxW, maxH))

def detectar_rectangulo_automatico(ruta_imagen, area_min=1000):
    img = cv2.imread(ruta_imagen)
    if img is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {ruta_imagen}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 2. Detección de bordes
    edges = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations=1)

    # 3. Encuentra contornos
    contornos, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # 4. Filtrado de cuadriláteros y selección del mayor
    mayor_area = 0
    mejor_approx = None
    for cnt in contornos:
        area = cv2.contourArea(cnt)
        if area < area_min:
            continue
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4 and cv2.isContourConvex(approx) and area > mayor_area:
            mayor_area = area
            mejor_approx = approx

    # 5. Dibujo y extracción
    resultado = img.copy()
    if mejor_approx is not None:
        cv2.polylines(resultado, [mejor_approx], True, (0, 255, 0), 3)
        # perspectiva enderezada
        recortado = four_point_transform(img, mejor_approx)
        return resultado, recortado, mejor_approx.reshape(4, 2)
    else:
        return resultado, None, None

if __name__ == "__main__":
    # 1) Carga correcta de la imagen original
    ruta = "./test.jpg"
    img = cv2.imread(ruta)
    if img is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen: {ruta}")

    # 2) Detectar el rectángulo blanco y obtener sus vértices
    con_rect, rec, pts = detectar_rectangulo_automatico(ruta)

    # Mostrar resultado de la detección de rectángulo
    cv2.imshow("Detección Automática", con_rect)

    if pts is not None:
        print("Vértices del rectángulo detectado:")
        for (x, y) in pts:
            print(f"  ({x:.1f}, {y:.1f})")

        # 3) Definir rango HSV para el color azul (ajusta si tu punto es más brillante u oscuro)
        lower_blue = (90,  50,  50)
        upper_blue = (140, 255, 255)

        # coords = get_color_point_coords(img, pts, lower_blue, upper_blue, area_min=50)

        pts_unit = np.array([[0, 0],
                             [rec.shape[1]-1, 0],
                             [rec.shape[1]-1, rec.shape[0]-1],
                             [0, rec.shape[0]-1]], dtype="float32")
        coords = get_color_point_coords(rec, pts_unit, lower_blue, upper_blue, area_min=50)

        if coords:
            cx, cy = coords
            print(f"Punto azul en marco del rectángulo: x={cx:.1f}, y={cy:.1f}")
            # Podemos dibujarlo sobre la vista enderezada para verificar
            vis = rec.copy() if rec is not None else img.copy()
            cv2.circle(vis, (int(cx), int(cy)), 8, (0,0,255), -1)
            cv2.imshow("Ubicación del Punto Azul", vis)
        else:
            print("No se detectó ningún punto azul dentro del rectángulo.")
            # Para depurar, muestra la máscara
            mask_debug = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            mask_debug = cv2.inRange(mask_debug, np.array(lower_blue), np.array(upper_blue))
            cv2.imshow("Máscara Azul (original)", mask_debug)

        # Mostrar bird’s-eye si existe
        if rec is not None:
            cv2.imshow("Perspectiva Enderezada", rec)

    else:
        print("No se encontró ningún rectángulo válido.")

    cv2.waitKey(0)
    cv2.destroyAllWindows()
