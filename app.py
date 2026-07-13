"""
app.py — Thin entry point (development only).
Production uses wsgi.py with Gunicorn.
"""
import os
from wanderai.app import create_app
from wanderai.ai.pipeline import init_pipeline

config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)

# Initialize AI pipeline
with app.app_context():
    try:
        from wanderai.extensions import cache
        init_pipeline(app.config, cache=cache)
    except Exception as e:
        print(f"⚠️  AI pipeline init warning: {e}")

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    print(f"🌍 WanderAI v2.0 starting on http://localhost:{port}")
    print(f"   Model  : {app.config.get('AI_PRIMARY_MODEL', 'not set')}")
    print(f"   Env    : {config_name}")
    app.run(debug=debug, host="0.0.0.0", port=port)
