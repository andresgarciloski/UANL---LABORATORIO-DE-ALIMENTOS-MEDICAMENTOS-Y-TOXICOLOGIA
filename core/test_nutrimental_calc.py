from decimal import Decimal, ROUND_HALF_UP

def round_half_up(val: float) -> int:
    if val is None:
        return 0
    v = float(val)
    if v < 0:
        v = abs(v)
    if v < 0.5:
        return 0
    return int(Decimal(str(v)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))

def regla_sodio(mg: float) -> int:
    v = float(mg)
    if v < 5:
        return 0
    if v < 140:
        # redondeo al múltiplo de 5 más cercano
        return int(round(v / 5.0) * 5)
    return int(round(v / 10.0) * 10)

def calcular(data: dict):
    proteina_raw = float(data['proteina'])
    grasa_total_raw = float(data['grasa_total'])
    fibra_raw = float(data['fibra_dietetica'])
    azucares_raw = float(data['azucares'])
    azucares_anadidos_raw = float(data['azucares_anadidos'])
    humedad_raw = float(data['humedad'])
    cenizas_raw = float(data['cenizas'])
    acidos_sat_pct = float(data['acidos_grasos_saturados'])
    sodio_raw = float(data['sodio'])
    grasa_trans_raw = float(data['grasa_trans'])
    porcion = float(data['porcion'])
    contenido_neto = float(data['contenido_neto'])

    grasa_saturada_cruda = grasa_total_raw * acidos_sat_pct / 100.0
    hidratos_totales_raw = 100 - (humedad_raw + cenizas_raw + proteina_raw + grasa_total_raw)
    carbo_balance_raw = max(0, hidratos_totales_raw - fibra_raw)

    # Redondeos por 100g
    proteina_100 = round_half_up(proteina_raw)
    grasa_total_100 = round_half_up(grasa_total_raw)
    grasa_saturada_100 = round_half_up(grasa_saturada_cruda)
    fibra_100 = round_half_up(fibra_raw)
    azucares_100 = round_half_up(azucares_raw)
    azucares_anadidos_100 = round_half_up(azucares_anadidos_raw)
    humedad_100 = round_half_up(humedad_raw)
    cenizas_100 = round_half_up(cenizas_raw)
    carbo_disp_100 = round_half_up(carbo_balance_raw)
    sodio_100 = regla_sodio(sodio_raw)
    grasa_trans_100 = round_half_up(grasa_trans_raw)

    energia_kcal_100 = int(round(((proteina_100 + carbo_disp_100) * 4 + grasa_total_100 * 9)/10.0)*10)
    energia_kj_100 = (proteina_100 + carbo_disp_100) * 17 + grasa_total_100 * 37

    factor = porcion / 100.0
    proteina_p = round_half_up(proteina_100 * factor)
    grasa_total_p = round_half_up(grasa_total_100 * factor)
    grasa_saturada_p = round_half_up(grasa_saturada_100 * factor)
    fibra_p = round_half_up(fibra_100 * factor)
    azucares_p = round_half_up(azucares_100 * factor)
    azucares_anadidos_p = round_half_up(azucares_anadidos_100 * factor)
    carbo_disp_p = round_half_up(carbo_disp_100 * factor)
    sodio_p = regla_sodio(sodio_raw * factor)
    grasa_trans_p = round_half_up(grasa_trans_raw * factor)
    energia_kcal_p = int(round(((proteina_p + carbo_disp_p) * 4 + grasa_total_p * 9)/10.0)*10)
    energia_kj_p = (proteina_p + carbo_disp_p) * 17 + grasa_total_p * 37

    factor_env = contenido_neto / 100.0
    energia_kcal_env = int(round(energia_kcal_100 * factor_env))
    energia_kj_env = int(round(energia_kj_100 * factor_env))

    return {
        'por_100g': {
            'energia_kcal': energia_kcal_100,
            'energia_kj': energia_kj_100,
            'proteina': proteina_100,
            'grasa_total': grasa_total_100,
            'grasa_saturada': grasa_saturada_100,
            'grasa_trans': grasa_trans_100,
            'carbohidratos_disponibles': carbo_disp_100,
            'azucares': azucares_100,
            'azucares_anadidos': azucares_anadidos_100,
            'fibra_dietetica': fibra_100,
            'sodio': sodio_100,
        },
        'por_porcion': {
            'energia_kcal': energia_kcal_p,
            'energia_kj': energia_kj_p,
            'proteina': proteina_p,
            'grasa_total': grasa_total_p,
            'grasa_saturada': grasa_saturada_p,
            'grasa_trans': grasa_trans_p,
            'carbohidratos_disponibles': carbo_disp_p,
            'azucares': azucares_p,
            'azucares_anadidos': azucares_anadidos_p,
            'fibra_dietetica': fibra_p,
            'sodio': sodio_p,
        },
        'por_envase': {
            'energia_kcal': energia_kcal_env,
            'energia_kj': energia_kj_env,
        }
    }

if __name__ == '__main__':
    datos = {
        'humedad': 9.34,
        'cenizas': 2.0,
        'proteina': 8.88,
        'grasa_total': 0.84,
        'grasa_trans': 10,
        'fibra_dietetica': 0,
        'azucares': 46.35,
        'azucares_anadidos': 6.35,
        'sodio': 143,
        'acidos_grasos_saturados': 69.97,
        'porcion': 20,
        'contenido_neto': 200,
    }
    r = calcular(datos)
    from pprint import pprint
    pprint(r)
