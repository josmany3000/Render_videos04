# app.py
from flask import Flask, request, jsonify
import os # Para acceder a variables de entorno como la clave de API

app = Flask(__name__)

# --- Función para la lógica de IA y generación de JSON ---
def apply_ai_video_editing_logic(frontend_data: dict) -> dict:
    """
    Esta función procesa los datos de la interfaz y genera el JSON final
    para la edición de video, integrando la lógica de IA.

    Aquí es donde integrarías las llamadas a las APIs de Google AI.
    """
    output_json = {
        "project_settings": {
            "duration_seconds": frontend_data.get("video_duration", 60),
            "language": frontend_data.get("language", "es"),
            "niche": frontend_data.get("niche", "General"),
            "resolution": frontend_data.get("resolution", "1080p"),
            "input_type": frontend_data.get("input_type", "script"),
            "ai_enhancements_enabled": frontend_data.get("ai_enhancements", False)
        },
        "media_assets": [],
        "audio_tracks": {
            "voiceover": [],
            "background_music": {},
            "sound_effects": []
        },
        "timeline": []
    }

    current_time = 0.0
    asset_id_counter = 1
    voiceover_id_counter = 1
    sfx_id_counter = 1

    # --- EJEMPLO DE INTEGRACIÓN CON IA DE GOOGLE (Gemini API) ---
    # Para usar esto, necesitarías:
    # 1. Instalar la librería: pip install google-generativeai
    # 2. Configurar tu API_KEY (por ejemplo, como variable de entorno en Render)
    # import google.generativeai as genai
    # GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    # if GOOGLE_API_KEY:
    #     genai.configure(api_key=GOOGLE_API_KEY)
    #     model = genai.GenerativeModel('gemini-pro')
    #
    #     # Ejemplo: Usar IA para refinar un script o generar ideas
    #     # response = model.generate_content(f"Refina este script para un video corto: {frontend_data.get('input_topic', frontend_data.get('input_script'))}")
    #     # refined_script = response.text
    # else:
    #     # print("GOOGLE_API_KEY no configurada. La funcionalidad de IA de Google estará limitada.")
    #     pass
    # --- FIN EJEMPLO DE INTEGRACIÓN ---

    # Procesar pistas de fondo
    background_music_url = frontend_data.get("background_music_url")
    background_music_volume = frontend_data.get("background_music_volume", 0.5)
    if background_music_url:
        bg_music_asset_id = f"bg_music_{asset_id_counter}"
        output_json["media_assets"].append({
            "id": bg_music_asset_id,
            "type": "audio",
            "url": background_music_url
        })
        output_json["audio_tracks"]["background_music"] = {
            "asset_id": bg_music_asset_id,
            "url": background_music_url,
            "volume": background_music_volume
        }
        asset_id_counter += 1

    # Procesar efectos de sonido globales
    for sfx_data in frontend_data.get("sound_effects", []):
        sfx_url = sfx_data.get("url")
        sfx_volume = sfx_data.get("volume", 1.0)
        sfx_description = sfx_data.get("description", "")
        sfx_start_time = sfx_data.get("start_time", 0.0)

        if sfx_url:
            sfx_asset_id = f"sfx_{sfx_id_counter}"
            output_json["media_assets"].append({
                "id": sfx_asset_id,
                "type": "audio",
                "url": sfx_url
            })
            output_json["audio_tracks"]["sound_effects"].append({
                "asset_id": sfx_asset_id,
                "url": sfx_url,
                "description": sfx_description,
                "volume": sfx_volume,
                "start_time_seconds": sfx_start_time
            })
            sfx_id_counter += 1

    # Procesar escenas
    for i, scene_data in enumerate(frontend_data.get("scenes", [])):
        scene_id = f"scene_{i+1}"
        scene_script = scene_data.get("script", "")
        scene_duration = scene_data.get("duration", 5.0)
        transition_type = scene_data.get("transition_type", "cut")
        transition_duration = scene_data.get("transition_duration", 0.5)

        visual_elements = []
        audio_elements = []

        # Procesar medios visuales de la escena
        for media_item in scene_data.get("media", []):
            media_url = media_item.get("url")
            media_type = media_item.get("type", "image")
            
            if media_url:
                media_asset_id = f"media_{asset_id_counter}"
                output_json["media_assets"].append({
                    "id": media_asset_id,
                    "type": media_type,
                    "url": media_url
                })
                visual_elements.append({
                    "asset_id": media_asset_id,
                    "type": "main_clip",
                    "start_time_in_scene": 0.0,
                    "duration_in_scene": scene_duration,
                    "effect": "none"
                })
                asset_id_counter += 1

        # Procesar audios de la escena (voiceover)
        voiceover_url = scene_data.get("audio_url")
        voiceover_volume = scene_data.get("audio_volume", 1.0)
        if voiceover_url:
            vo_asset_id = f"vo_{voiceover_id_counter}"
            output_json["media_assets"].append({
                "id": vo_asset_id,
                "type": "audio",
                "url": voiceover_url
            })
            output_json["audio_tracks"]["voiceover"].append({
                "id": vo_asset_id,
                "text_segment": scene_script,
                "url": voiceover_url,
                "start_time_seconds": current_time,
                "duration_seconds": scene_duration
            })
            audio_elements.append({
                "asset_id": vo_asset_id,
                "type": "voiceover",
                "start_time_in_scene": 0.0,
                "volume": voiceover_volume
            })
            voiceover_id_counter += 1

        # Añadir la escena al timeline
        output_json["timeline"].append({
            "type": "scene",
            "id": scene_id,
            "start_time_seconds": current_time,
            "duration_seconds": scene_duration,
            "script": scene_script,
            "visual_elements": visual_elements,
            "audio_elements": audio_elements,
            "transition_to_next_scene": {
                "type": transition_type,
                "duration_seconds": transition_duration
            }
        })
        current_time += scene_duration

    return output_json

@app.route('/generate-video-json', methods=['POST'])
def generate_video_json():
    """
    Endpoint para recibir los datos de la interfaz
    y generar el JSON de instrucciones de video.
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    frontend_data = request.get_json()

    try:
        video_instructions_json = apply_ai_video_editing_logic(frontend_data)
        
        # Opcional: Para forzar la descarga en el navegador, podrías añadir headers
        # from flask import make_response
        # response = make_response(jsonify(video_instructions_json))
        # response.headers["Content-Disposition"] = "attachment; filename=video_instructions.json"
        # response.headers["Content-Type"] = "application/json"
        # return response

        return jsonify(video_instructions_json), 200
    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"error": "Error interno al generar las instrucciones de video."}), 500

@app.route('/')
def home():
    return "Backend de generación de JSON de video operativo."

if __name__ == '__main__':
    # Usar host='0.0.0.0' es necesario para que sea accesible en Render
    app.run(debug=False, host='0.0.0.0', port=os.getenv('PORT', 5000)) # Usa el puerto de Render si está disponible
