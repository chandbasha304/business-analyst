import os
import sys

def main():
    print("==================================================================")
    print("             ProjectLens AI - Local Enterprise Assistant           ")
    print("==================================================================")
    
    # 1. Ensure .env file exists
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        print("[System] No '.env' file detected. Generating default configuration template...")
        try:
            with open(env_path, "w") as f:
                f.write("# ProjectLens AI Local Configuration\n")
                f.write("# Paste your live Google Gemini API key below to activate agentic features.\n")
                f.write("GEMINI_API_KEY=\n")
                f.write("PORT=8080\n")
                f.write("HOST=127.0.0.1\n")
            print(f"[System] Success. Created default config: '{env_path}'")
            print("[System] IMPORTANT: Open '.env' and paste your GEMINI_API_KEY to activate live reasoning.")
        except Exception as e:
            print(f"[System] Warning: Could not create default config: {e}")
            
    # 2. Check dependencies
    try:
        import fastapi
        import uvicorn
        import jwt
        import numpy
    except ImportError as e:
        print(f"\n[System] Error: Missing Python dependencies: {e}")
        print("[System] Please run: pip install -r requirements.txt")
        sys.exit(1)
        
    # 3. Read host/port from .env if available
    port = 8080
    host = "127.0.0.1"
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    if k == "PORT":
                        port = int(v)
                    elif k == "HOST":
                        host = v
                        
    # 4. Launch FastAPI Uvicorn Server
    print(f"[System] Booting FastAPI application server...")
    print(f"[System] Access Web Dashboard: http://{host}:{port}/")
    print("==================================================================\n")
    
    try:
        uvicorn.run("backend.main:app", host=host, port=port, reload=True)
    except KeyboardInterrupt:
        print("\n[System] Server terminated by user request. Exiting.")
    except Exception as e:
        print(f"\n[System] Failed to launch server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
