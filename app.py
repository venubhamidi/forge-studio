#!/usr/bin/env python3
"""
Forge Studio - OpenAPI to MCP Tool Registry for IBM Context Forge
Transform REST APIs into Model Context Protocol tools
"""

import streamlit as st
import tempfile
import os
from pathlib import Path
from register_openapi import OpenAPIToMCP

# Page config
st.set_page_config(
    page_title="Forge Studio",
    page_icon="🔨",
    layout="centered"
)

# Authentication credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Alekhya0516@654321"

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Login form
if not st.session_state.authenticated:
    st.title("🔐 Login to Forge Studio")
    st.markdown("Please authenticate to access the OpenAPI registry")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    st.stop()

# Logout button in sidebar
with st.sidebar:
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()
    st.markdown("---")

# Title and description
st.title("🔨 Forge Studio")
st.markdown("Transform OpenAPI specs into MCP tools for IBM Context Forge")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    gateway_url = st.text_input(
        "Gateway URL",
        value=os.getenv("GATEWAY_URL", "http://gateway:4444"),
        help="URL of the MCP Gateway instance"
    )

    bearer_token = st.text_input(
        "Bearer Token",
        type="password",
        value=os.getenv("BEARER_TOKEN", ""),
        help="JWT token for authentication"
    )

    st.markdown("---")
    st.markdown("### 📚 About")
    st.markdown("""
    Upload an OpenAPI 3.0 specification (YAML or JSON) to automatically:
    - Parse all endpoints
    - Register them as MCP tools
    - Create a virtual MCP server
    """)

# Main content
st.header("📁 Upload OpenAPI Specification")

# File uploader
uploaded_file = st.file_uploader(
    "Choose an OpenAPI spec file",
    type=['yaml', 'yml', 'json'],
    help="Upload your OpenAPI 3.0 specification"
)

# Optional API name
api_name = st.text_input(
    "API Name (optional)",
    placeholder="Leave empty to use name from spec",
    help="Custom name for the API server"
)

# Display file info if uploaded
if uploaded_file is not None:
    st.info(f"📄 **File:** {uploaded_file.name} ({uploaded_file.size} bytes)")

# Register button
if st.button("🔧 Register API", type="primary", disabled=uploaded_file is None):
    if not bearer_token:
        st.error("❌ Bearer token is required!")
    else:
        with st.spinner("Registering API..."):
            try:
                # Save uploaded file to temp location
                with tempfile.NamedTemporaryFile(
                    mode='wb',
                    suffix=Path(uploaded_file.name).suffix,
                    delete=False
                ) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                # Create converter and register
                converter = OpenAPIToMCP(gateway_url, bearer_token)

                # Capture output in expander
                with st.expander("📋 Registration Log", expanded=True):
                    # Register the spec
                    result = converter.register_openapi_spec(
                        tmp_path,
                        api_name if api_name else None
                    )

                # Clean up temp file
                os.unlink(tmp_path)

                # Success message
                st.success("✅ API Registered Successfully!")

                # Display results
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Tools Registered", result['tool_count'])
                with col2:
                    st.metric("API Name", result['api_name'])
                with col3:
                    st.metric("Server UUID", result['server_uuid'][:8] + "...")

                # Show endpoint
                st.markdown("### 📡 MCP Endpoint")
                endpoint = f"{gateway_url}/servers/{result['server_uuid']}/mcp"
                st.code(endpoint, language="text")

                # Show configuration
                with st.expander("🔧 Configuration Details"):
                    st.json({
                        "server_uuid": result['server_uuid'],
                        "gateway_url": gateway_url,
                        "streamable_http_endpoint": endpoint,
                        "tool_count": result['tool_count'],
                        "api_name": result['api_name'],
                        "base_url": result['base_url']
                    })

            except Exception as e:
                st.error(f"❌ Registration Failed!")
                st.exception(e)

# Show existing servers section
st.markdown("---")
st.header("🖥️ Registered Servers")

if bearer_token and st.button("🔄 Refresh Servers"):
    try:
        import requests

        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(f"{gateway_url}/servers", headers=headers)
        response.raise_for_status()
        servers = response.json()

        if servers:
            for server in servers:
                with st.expander(f"📡 {server.get('name', 'Unknown')}"):
                    st.json(server)
        else:
            st.info("No servers registered yet.")

    except Exception as e:
        st.error(f"Failed to fetch servers: {e}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <small>Powered by IBM MCP Context Forge</small>
    </div>
    """,
    unsafe_allow_html=True
)
