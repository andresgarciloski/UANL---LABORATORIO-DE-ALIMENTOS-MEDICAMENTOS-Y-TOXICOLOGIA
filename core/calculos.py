import math
from decimal import Decimal, ROUND_HALF_UP

def _round_half_up(val):
    try:
        v = float(val)
    except Exception:
        return 0
    if v < 0.5:
        return 0
    return int(Decimal(str(v)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def _round_half_up_05(val):
    try:
        v = float(val)
    except Exception:
        return 0.0
    return float(Decimal(str(v)).quantize(Decimal('0.5'), rounding=ROUND_HALF_UP))

def aplicar_regla_redondeo_sodio(valor):
    try:
        v = float(valor)
    except Exception:
        return 0
    if v < 5:
        return 0
    elif v < 140:
        return int(round(v / 5) * 5)
    else:
        return int(round(v / 10) * 10)

def aplicar_redondeo_energia(valor_kcal):
    try:
        v = float(valor_kcal)
    except Exception:
        return 0
    return int(round(v / 10.0) * 10)

def calcular_nutrimental(data):
    """Calcula valores nutrimentales a partir de 'data' (diccionario)."""
    half_up = _round_half_up

    def _f(key):
        try:
            return float(data.get(key, 0) or 0)
        except Exception:
            return 0.0

    proteina_raw = _f('proteina')
    grasa_total_raw = _f('grasa_total')
    fibra_raw = _f('fibra_dietetica')
    azucares_raw = _f('azucares')
    azucares_anadidos_raw = _f('azucares_anadidos')
    humedad_raw = _f('humedad')
    cenizas_raw = _f('cenizas')
    acidos_sat_pct = _f('acidos_grasos_saturados')
    sodio_raw = _f('sodio')          # mg
    grasa_trans_raw = _f('grasa_trans')  # mg

    grasa_saturada_cruda = grasa_total_raw * acidos_sat_pct / 100.0 if grasa_total_raw and acidos_sat_pct else 0.0
    hidratos_totales_raw = 100 - (humedad_raw + cenizas_raw + proteina_raw + grasa_total_raw)
    carbo_balance_raw = hidratos_totales_raw - fibra_raw
    if carbo_balance_raw < 0:
        carbo_balance_raw = 0

    humedad_100g = half_up(humedad_raw)
    cenizas_100g = half_up(cenizas_raw)
    proteina_100g = half_up(proteina_raw)
    grasa_total_100g = half_up(grasa_total_raw)
    fibra_dietetica_100g = half_up(fibra_raw)
    azucares_100g = half_up(azucares_raw)
    azucares_anadidos_100g = half_up(azucares_anadidos_raw)
    grasa_saturada_100g = _round_half_up_05(grasa_saturada_cruda) if grasa_saturada_cruda else 0.0
    carbohidratos_disponibles_100g = half_up(carbo_balance_raw)
    sodio_100g = aplicar_regla_redondeo_sodio(sodio_raw)
    grasa_trans_100g = half_up(grasa_trans_raw)

    total_componentes_base = humedad_raw + cenizas_raw + proteina_raw + grasa_total_raw + fibra_raw
    aviso_componentes_excedidos = total_componentes_base > 101

    energia_kcal_100g = (proteina_100g + carbohidratos_disponibles_100g) * 4 + grasa_total_100g * 9
    energia_kcal_100g = aplicar_redondeo_energia(energia_kcal_100g)
    energia_kj_100g = (proteina_100g + carbohidratos_disponibles_100g) * 17 + grasa_total_100g * 37

    porcion = _f('porcion')
    factor = porcion / 100.0 if porcion else 0
    proteina_porcion = half_up(proteina_100g * factor)
    grasa_total_porcion = half_up(grasa_total_100g * factor)
    grasa_saturada_porcion = _round_half_up_05(grasa_saturada_cruda * factor) if grasa_saturada_cruda else 0.0
    fibra_dietetica_porcion = half_up(fibra_dietetica_100g * factor)
    azucares_porcion = half_up(azucares_100g * factor)
    azucares_anadidos_porcion = half_up(azucares_anadidos_100g * factor)
    carbohidratos_disponibles_porcion = half_up(carbohidratos_disponibles_100g * factor)
    sodio_porcion = aplicar_regla_redondeo_sodio(sodio_raw * factor)
    grasa_trans_porcion = half_up(grasa_trans_raw * factor)
    energia_kcal_porcion = (proteina_porcion + carbohidratos_disponibles_porcion) * 4 + grasa_total_porcion * 9
    energia_kcal_porcion = aplicar_redondeo_energia(energia_kcal_porcion)
    energia_kj_porcion = (proteina_porcion + carbohidratos_disponibles_porcion) * 17 + grasa_total_porcion * 37

    porciones_envase = None
    por_envase = None
    contenido_neto_txt = data.get('contenido_neto')
    if contenido_neto_txt:
        try:
            contenido_neto = float(contenido_neto_txt)
            porciones_envase = contenido_neto / porcion if porcion else None
            factor_env = contenido_neto / 100.0
            energia_kcal_envase = energia_kcal_100g * factor_env
            energia_kj_envase = energia_kj_100g * factor_env
            por_envase = {
                'energia_kcal': int(round(energia_kcal_envase)),
                'energia_kj': int(round(energia_kj_envase))
            }
        except Exception:
            porciones_envase = None

    resultados = {
        'por_100g': {
            'proteina': proteina_100g,
            'grasa_total': grasa_total_100g,
            'grasa_saturada': grasa_saturada_100g,
            'grasa_trans': grasa_trans_100g,
            'carbohidratos_disponibles': carbohidratos_disponibles_100g,
            'azucares': azucares_100g,
            'azucares_anadidos': azucares_anadidos_100g,
            'fibra_dietetica': fibra_dietetica_100g,
            'sodio': sodio_100g,
            'energia_kcal': energia_kcal_100g,
            'energia_kj': energia_kj_100g
        },
        'por_porcion': {
            'proteina': proteina_porcion,
            'grasa_total': grasa_total_porcion,
            'grasa_saturada': grasa_saturada_porcion,
            'grasa_trans': grasa_trans_porcion,
            'carbohidratos_disponibles': carbohidratos_disponibles_porcion,
            'azucares': azucares_porcion,
            'azucares_anadidos': azucares_anadidos_porcion,
            'fibra_dietetica': fibra_dietetica_porcion,
            'sodio': sodio_porcion,
            'energia_kcal': energia_kcal_porcion,
            'energia_kj': energia_kj_porcion
        }
    }
    if porciones_envase is not None:
        resultados['porciones_envase'] = porciones_envase
    if por_envase is not None:
        resultados['por_envase'] = por_envase
    resultados['es_porcion_100g'] = (porcion == 100.0)
    if aviso_componentes_excedidos:
        resultados['warning_componentes'] = True
    return resultados

def calcular_sellos_advertencia(resultados, es_liquida=False, es_bebida_sin_calorias=False):
    """Calcula sellos a partir de resultados ya calculados."""
    sellos = {
        "exceso_calorias": False,
        "exceso_azucares": False,
        "exceso_grasas_saturadas": False,
        "exceso_grasas_trans": False,
        "exceso_sodio": False
    }
    por100 = resultados.get("por_100g", {})
    calorias = float(por100.get("energia_kcal", 0) or 0)
    azucares_g = float(por100.get("azucares", 0) or 0)
    grasa_sat_g = float(por100.get("grasa_saturada", 0) or 0)
    grasa_trans_mg = float(por100.get("grasa_trans", 0) or 0)
    sodio_mg = float(por100.get("sodio", 0) or 0)

    if es_liquida:
        if calorias >= 70:
            sellos["exceso_calorias"] = True
    else:
        if calorias >= 275:
            sellos["exceso_calorias"] = True
    if (azucares_g * 4) >= 8:
        sellos["exceso_calorias"] = True

    if calorias > 0:
        if (azucares_g * 4) >= (0.10 * calorias):
            sellos["exceso_azucares"] = True
        if (grasa_sat_g * 9) >= (0.10 * calorias):
            sellos["exceso_grasas_saturadas"] = True
        energia_trans_kcal = (grasa_trans_mg / 1000.0) * 9.0
        if energia_trans_kcal >= (0.01 * calorias):
            sellos["exceso_grasas_trans"] = True

    if sodio_mg >= 300:
        sellos["exceso_sodio"] = True
    elif calorias >= 0 and sodio_mg >= calorias:
        sellos["exceso_sodio"] = True
    elif es_bebida_sin_calorias and sodio_mg >= 45:
        sellos["exceso_sodio"] = True

    return sellos