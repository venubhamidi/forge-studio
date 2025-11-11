# Streamlit UI for MCP Gateway

Web interface for registering OpenAPI specifications as MCP tools.

## Features

- 📁 **File Upload** - Drag & drop or browse for OpenAPI specs (YAML/JSON)
- ✅ **Success/Error Handling** - Clear feedback on registration status
- 📊 **Dashboard** - View registered servers and tools
- 🔧 **Configuration** - Easy gateway URL and token management
- 📋 **Detailed Logs** - See what's happening during registration

## Quick Start

### Using Docker Compose (Recommended)

```bash
# From parent directory
docker-compose up -d

# Open browser
open http://localhost:8501
```

### Using Docker Directly

```bash
# Build
docker build -t streamlit-ui .

# Run
docker run -d \
  --name streamlit-ui \
  -p 8501:8501 \
  -e GATEWAY_URL=http://gateway:4444 \
  -e BEARER_TOKEN=your-token-here \
  streamlit-ui
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

## Usage

1. **Open the UI**: http://localhost:8501
2. **Configure**:
   - Set Gateway URL (default: `http://gateway:4444`)
   - Enter Bearer Token (get from gateway)
3. **Upload OpenAPI Spec**:
   - Choose YAML or JSON file
   - Optionally set custom API name
4. **Click Register**:
   - View registration progress
   - See success/error messages
   - Get MCP endpoint URL

## Environment Variables

- `GATEWAY_URL` - MCP Gateway URL (default: `http://gateway:4444`)
- `BEARER_TOKEN` - JWT token for authentication

## Screenshots

### Main Interface
- File uploader
- Configuration sidebar
- Register button
- Success metrics

### Results Display
- Tool count
- Server UUID
- MCP endpoint URL
- Full configuration JSON

## Development

The app uses:
- **Streamlit** - Web framework
- **register_openapi.py** - Registration logic (reused from CLI)
- **requests** - HTTP client
- **PyYAML** - YAML parsing
# forge-studio
