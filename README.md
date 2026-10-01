# 🧭 SucesIA · Relevo generacional con IA

Herramienta de RR. HH. para anticipar las jubilaciones y preparar el relevo generacional. A partir de la información que RR. HH. ya tiene:

1. **Detecta quién se va a jubilar** en los próximos años, destacando los puestos clave.
2. **Recomienda a las 5 personas** mejor situadas para cada relevo.
3. **Indica sus gaps** frente a la descripción del puesto.
4. **Propone un plan de formación 70-20-10** (experiencial, social y formal) que termina antes de la jubilación.
5. **Registra la decisión** del comité de talento.

> La herramienta recomienda; la decisión es siempre de una persona. La edad solo se usa para prever jubilaciones, nunca para puntuar candidatos.

Proyecto del máster en People Analytics. Los datos de ejemplo son 100 % ficticios.

---

## Qué datos necesita

Todos los archivos son Excel (se lee la primera hoja). Se suben desde la barra lateral eligiendo **Mis archivos**, o se usan los de ejemplo eligiendo **Datos de ejemplo**.

| Archivo | Columnas obligatorias | Ejemplo incluido |
| --- | --- | --- |
| Plantilla | id_empleado, nombre, fecha_nacimiento (o edad), fecha_incorporacion, antiguedad_puesto_anios, puesto, area, interes_cambio_puesto (Sí/No) | `ejemplo_plantilla.xlsx` |
| Organigrama | puesto, area, reporta_a, nivel_jerarquico (1 = el más alto), puesto_clave (Sí/No) | `ejemplo_organigrama.xlsx` |
| Diccionario de competencias | codigo, competencia, definicion, nivel_1 … nivel_5 | `ejemplo_diccionario_competencias.xlsx` |
| Descripción de puestos | puesto, codigo, nivel_requerido (1-5), peso (opcional: mision) | `ejemplo_descripcion_puestos.xlsx` |
| Desempeño año anterior | id_empleado, desempeno_global (1-5), potencial (1-3), una columna por competencia (C01…), comentario_evaluador | `ejemplo_desempeno_2024.xlsx` |
| Desempeño último año | igual que el anterior | `ejemplo_desempeno_2025.xlsx` |

Los ejemplos se pueden volver a generar con `python generar_datos_ejemplo.py`.

## Cómo funciona

| Paso | Regla |
| --- | --- |
| Jubilaciones | Fecha en que cada persona cumple la edad de jubilación (67 por defecto, configurable) dentro del horizonte elegido (5 años por defecto) |
| Quién puede ser relevo | Personas de un nivel jerárquico inferior al puesto, con valoración ≥ 3 e interés en cambiar de puesto. Las demás se muestran aparte con el motivo |
| Puntuación 0-100 | 50 % ajuste competencial + 20 % desempeño medio de 2 años + 20 % potencial + 10 % evolución (pesos editables) |
| Gaps | Nivel requerido − nivel actual, ordenados por gap × peso |
| Preparación | Listo ahora (ajuste ≥ 90 % y ningún gap ≥ 2) · 1-2 años (ajuste ≥ 75 % y como máximo un gap ≥ 2) · 3+ años |
| Plan 70-20-10 | Proyectos y retos (70) · mentoría con quien se jubila, coaching, observación y feedback (20) · cursos, talleres, e-learning y lecturas (10). El reparto se mide en horas de dedicación |
| IA | Explica el ranking y diseña el plan. Sin clave de API, ambas cosas se hacen con reglas |

## Archivos

```
app.py                      interfaz Streamlit (5 pestañas)
datos.py                    carga y validación de los Excel, cálculo de jubilaciones
matching.py                 puntuación, gaps y preparación
plan_formacion.py           plan 70-20-10 por reglas
llm.py                      IA generativa (OpenAI o Anthropic)
graficos.py                 gráficos Plotly
test_sucesia.py             pruebas (python -m pytest)
generar_datos_ejemplo.py    crea los Excel de ejemplo
ejemplo_*.xlsx              6 Excel de ejemplo con datos ficticios
requirements.txt            librerías
secrets.toml.example        plantilla para la clave de la IA
```

---

## Publicarla en Streamlit Community Cloud

1. **GitHub:** sube todos los archivos a la raíz de un repositorio público (por ejemplo, `sucesia`), sin carpetas.
2. Entra en [share.streamlit.io](https://share.streamlit.io) → **Create app** → **Deploy a public app from GitHub**.
3. Rellena: repositorio `tu-usuario/sucesia`, rama `main`, archivo `app.py`.
4. Abre **Advanced settings**, elige **Python 3.12** y, si tienes clave de IA, pega en **Secrets** las tres líneas de `secrets.toml.example` con tus datos.
5. Pulsa **Deploy**.

Si ya tenías la app publicada, basta con sustituir los archivos en GitHub: Streamlit se actualiza solo en uno o dos minutos.

## Ejecutarla en tu ordenador (opcional)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

## Comprobación rápida

- Pestaña 1: con los datos de ejemplo salen 6 jubilaciones en 5 años, 3 de ellas en puestos clave.
- Pestaña 3, relevo del Jefe/a de Mantenimiento: la primera recomendada es Laura Martín Sanz (89,5).
- El Director/a General y Pedro Castillo aparecen en *Personas apartadas*, con su motivo.
- Pestaña 5: el plan reparte las horas en torno a 70-20-10 y el calendario marca la fecha de jubilación.

## Cuidados

- **Supervisión humana:** la app recomienda; el comité decide y su decisión queda registrada.
- **Sin discriminación por edad:** la edad solo sirve para prever jubilaciones; nunca puntúa.
- **Privacidad:** a la IA solo se envían ids, puntuaciones, gaps y comentarios; nunca nombres.
- **AI Act:** una IA que influye en promociones es de alto riesgo; por eso las reglas son transparentes y editables.
- **Registro de decisiones:** en Streamlit Cloud el disco no es permanente; descarga el registro tras usarlo.
