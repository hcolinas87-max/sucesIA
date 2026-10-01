"""Pruebas de SucesIA con los datos de ejemplo:  python -m pytest"""
from datetime import date

import pandas as pd
import pytest

from datos import (ejemplo, jubilaciones, preparar_descripciones, preparar_diccionario, preparar_organigrama,
                   preparar_plantilla, unir_desempeno)
from matching import calcular_ranking, redondear
from plan_formacion import generar_plan_reglas

HOY = date(2026, 10, 1)


@pytest.fixture(scope="module")
def datos():
    plantilla = preparar_plantilla(ejemplo("plantilla"), HOY)
    organigrama = preparar_organigrama(ejemplo("organigrama"))
    diccionario = preparar_diccionario(ejemplo("diccionario"))
    descripciones = preparar_descripciones(ejemplo("descripciones"), diccionario)
    anterior, ultimo = unir_desempeno(ejemplo("desempeno_anterior"), ejemplo("desempeno_ultimo"),
                                      diccionario["codigo"].tolist())
    return plantilla, organigrama, diccionario, descripciones, anterior, ultimo


def test_redondeo():
    assert redondear(89.45) == 89.5


def test_jubilaciones(datos):
    plantilla, organigrama, *_ = datos
    jub = jubilaciones(plantilla, organigrama, 67, 5, HOY)
    assert {"E001", "E002", "E003"} <= set(jub["id_empleado"])
    assert set(jub[jub["puesto_clave"] == "Sí"]["id_empleado"]) == {"E001", "E002", "E003"}
    e001 = jub.set_index("id_empleado").loc["E001", "fecha_jubilacion"]
    assert e001 == pd.Timestamp("2028-03-15")


def test_ranking_mantenimiento(datos):
    plantilla, organigrama, diccionario, descripciones, anterior, ultimo = datos
    perfil = descripciones[descripciones["puesto"] == "Jefe/a de Mantenimiento"]
    niveles = dict(zip(organigrama["puesto"], organigrama["nivel_jerarquico"]))
    res = calcular_ranking(plantilla, anterior, ultimo, perfil, "E001", area_puesto="Mantenimiento",
                           niveles_puesto=niveles, nivel_objetivo=2)
    r = res["ranking"]
    assert r.iloc[0]["id_empleado"] == "E004"  # Laura Martín
    assert "E001" not in set(r["id_empleado"])
    assert res["excluidos"].set_index("id_empleado").loc["E006", "motivo_exclusion"] == "No quiere cambiar de puesto"
    assert len(r) >= 5
    ex = res["excluidos"].set_index("id_empleado")
    assert ex.loc["E014", "motivo_exclusion"] == "Ya ocupa un puesto de igual o mayor nivel"  # Director/a General


def test_edad_no_puntua(datos):
    plantilla, organigrama, diccionario, descripciones, anterior, ultimo = datos
    perfil = descripciones[descripciones["puesto"] == "Jefe/a de Mantenimiento"]
    base = calcular_ranking(plantilla, anterior, ultimo, perfil, "E001")["ranking"]
    mayor = plantilla.assign(fecha_nacimiento=pd.Timestamp("1950-01-01"), edad=76)
    otra = calcular_ranking(mayor, anterior, ultimo, perfil, "E001")["ranking"]
    assert base["indice"].tolist() == otra["indice"].tolist()


def test_plan_reglas(datos):
    plantilla, organigrama, diccionario, descripciones, anterior, ultimo = datos
    perfil = descripciones[descripciones["puesto"] == "Jefe/a de Mantenimiento"]
    res = calcular_ranking(plantilla, anterior, ultimo, perfil, "E001")
    plan = generar_plan_reglas("E004", res["brechas"]["E004"], "2028-03-15", "Jefe/a de Mantenimiento", hoy=HOY)
    acc = pd.DataFrame(plan["acciones"])
    assert set(acc["modelo_70_20_10"]) == {"70", "20", "10"}
    assert acc["accion"].str.contains("Mentoría").any()
    assert acc["tipo"].eq("Lectura").any()
    formacion = acc[acc["tipo"] != "Traspaso"]
    assert pd.to_datetime(formacion["fin"]).max() <= pd.Timestamp("2027-12-15")


def test_reparto_702010(datos):
    plantilla, organigrama, diccionario, descripciones, anterior, ultimo = datos
    from plan_formacion import reparto_702010
    perfil = descripciones[descripciones["puesto"] == "Jefe/a de Mantenimiento"]
    res = calcular_ranking(plantilla, anterior, ultimo, perfil, "E001")
    plan = generar_plan_reglas("E004", res["brechas"]["E004"], "2028-03-15", "Jefe/a de Mantenimiento", hoy=HOY)
    reparto = reparto_702010(plan["acciones"])
    assert 0.6 <= reparto["70"] <= 0.8 and reparto["20"] >= 0.1 and reparto["10"] >= 0.05
