"""
Copilot Bridge API Routes

REST API for Copilot <-> Abby <-> User collaboration.
"""

from flask import Blueprint, request, jsonify, send_from_directory
import logging
import os

from copilot_bridge import get_copilot_bridge

logger = logging.getLogger(__name__)

copilot_bp = Blueprint('copilot', __name__, url_prefix='/api/copilot')


@copilot_bp.route('/bridge-chat')
def bridge_chat_page():
    """Serve the three-way bridge chat interface"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_dir, 'bridge_chat.html')


@copilot_bp.route('/status', methods=['GET'])
def bridge_status():
    """Get bridge status"""
    try:
        bridge = get_copilot_bridge()
        return jsonify(bridge.get_status())
    except Exception as e:
        logger.error(f"Error getting bridge status: {e}")
        return jsonify({"error": str(e)}), 500


@copilot_bp.route('/channel', methods=['GET'])
def get_channel():
    """Get channel messages"""
    try:
        bridge = get_copilot_bridge()
        limit = request.args.get('limit', 50, type=int)
        sender = request.args.get('sender')
        
        messages = bridge.get_channel(limit=limit, sender=sender)
        return jsonify({"messages": messages, "count": len(messages)})
    except Exception as e:
        logger.error(f"Error getting channel: {e}")
        return jsonify({"error": str(e)}), 500


@copilot_bp.route('/message', methods=['POST'])
def post_message():
    """Post a message to the channel (from Copilot)"""
    try:
        bridge = get_copilot_bridge()
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({"error": "content required"}), 400
        
        sender = data.get('sender', 'copilot')
        msg = bridge.post_message(
            sender=sender,
            content=data['content'],
            msg_type=data.get('type', 'message'),
            metadata=data.get('metadata', {})
        )
        
        return jsonify({"message": "posted", "id": msg.id})
    except Exception as e:
        logger.error(f"Error posting message: {e}")
        return jsonify({"error": str(e)}), 500


@copilot_bp.route('/request', methods=['POST'])
def post_request():
    """Post a task request"""
    try:
        bridge = get_copilot_bridge()
        data = request.get_json()
        
        if not data or 'task' not in data:
            return jsonify({"error": "task required"}), 400
        
        sender = data.get('sender', 'copilot')
        
        if sender == 'copilot':
            msg = bridge.request_from_copilot(data['task'], data.get('context'))
        else:
            msg = bridge.request_from_abby(data['task'], data.get('context'))
        
        return jsonify({"message": "request posted", "id": msg.id})
    except Exception as e:
        logger.error(f"Error posting request: {e}")
        return jsonify({"error": str(e)}), 500


@copilot_bp.route('/pending', methods=['GET'])
def get_pending():
    """Get pending requests"""
    try:
        bridge = get_copilot_bridge()
        for_sender = request.args.get('for')
        
        requests = bridge.get_pending_requests(for_sender)
        return jsonify({"requests": requests, "count": len(requests)})
    except Exception as e:
        logger.error(f"Error getting pending requests: {e}")
        return jsonify({"error": str(e)}), 500


@copilot_bp.route('/respond/<request_id>', methods=['POST'])
def respond_to_request(request_id):
    """Respond to a pending request"""
    try:
        bridge = get_copilot_bridge()
        data = request.get_json()
        
        if not data or 'response' not in data:
            return jsonify({"error": "response required"}), 400
        
        sender = data.get('sender', 'abby')
        msg = bridge.respond_to_request(request_id, data['response'], sender)
        
        return jsonify({"message": "responded", "id": msg.id})
    except Exception as e:
        logger.error(f"Error responding to request: {e}")
        return jsonify({"error": str(e)}), 500


@copilot_bp.route('/code', methods=['POST'])
def share_code():
    """Share code between AIs"""
    try:
        bridge = get_copilot_bridge()
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({"error": "code required"}), 400
        
        msg = bridge.share_code(
            sender=data.get('sender', 'copilot'),
            code=data['code'],
            filename=data.get('filename'),
            language=data.get('language', 'python'),
            description=data.get('description', '')
        )
        
        return jsonify({"message": "code shared", "id": msg.id})
    except Exception as e:
        logger.error(f"Error sharing code: {e}")
        return jsonify({"error": str(e)}), 500


@copilot_bp.route('/context', methods=['GET'])
def get_context():
    """Get shared context"""
    try:
        bridge = get_copilot_bridge()
        key = request.args.get('key')
        
        context = bridge.get_context(key)
        return jsonify({"context": context})
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        return jsonify({"error": str(e)}), 500


@copilot_bp.route('/context', methods=['POST'])
def set_context():
    """Set shared context"""
    try:
        bridge = get_copilot_bridge()
        data = request.get_json()
        
        if not data or 'key' not in data or 'value' not in data:
            return jsonify({"error": "key and value required"}), 400
        
        bridge.set_context(
            key=data['key'],
            value=data['value'],
            sender=data.get('sender', 'system')
        )
        
        return jsonify({"message": "context set"})
    except Exception as e:
        logger.error(f"Error setting context: {e}")
        return jsonify({"error": str(e)}), 500


# ============ COPILOT DIRECT INTEGRATION ============
# These endpoints are designed for direct use by GitHub Copilot

@copilot_bp.route('/ask-abby', methods=['POST'])
def ask_abby():
    """
    Copilot asks Abby a question or sends a task.
    This is the main entry point for Copilot -> Abby communication.
    """
    try:
        bridge = get_copilot_bridge()
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "message required"}), 400
        
        # Post message to Abby
        msg = bridge.post_from_copilot(
            content=data['message'],
            msg_type=data.get('type', 'message'),
            metadata={
                "expecting_response": True,
                "context": data.get('context', {})
            }
        )
        
        return jsonify({
            "status": "sent",
            "message_id": msg.id,
            "note": "Abby will process this and respond. Check /api/copilot/channel for responses."
        })
    except Exception as e:
        logger.error(f"Error in ask-abby: {e}")
        return jsonify({"error": str(e)}), 500


@copilot_bp.route('/from-abby', methods=['GET'])
def from_abby():
    """
    Get messages from Abby to Copilot.
    Copilot should poll this to see Abby's responses.
    """
    try:
        bridge = get_copilot_bridge()
        limit = request.args.get('limit', 10, type=int)
        
        messages = bridge.get_messages_for_copilot(limit=limit)
        return jsonify({
            "messages": messages,
            "count": len(messages)
        })
    except Exception as e:
        logger.error(f"Error getting messages from Abby: {e}")
        return jsonify({"error": str(e)}), 500


@copilot_bp.route('/chat', methods=['POST'])
def copilot_chat():
    """
    Send a message to Abby and get a response.
    This is a synchronous endpoint that waits for Abby's full response.
    
    Request body:
        - message: The message to send to Abby
        - context: Optional context dictionary
    
    Returns:
        - response: Abby's full response
        - message_id: ID of the message in the channel
    """
    try:
        from api_server import get_streaming_conversation_instance
        
        bridge = get_copilot_bridge()
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "message required"}), 400
        
        message = data['message']
        extra_context = data.get('context', {})
        
        # Post to channel so it's recorded
        msg = bridge.post_from_copilot(message, "message", {
            "expecting_response": True
        })
        
        # Get streaming conversation and process
        sc = get_streaming_conversation_instance()
        if not sc:
            return jsonify({"error": "Abby is not available"}), 503
        
        # Build context with copilot flag
        context = {
            'from_copilot': True,
            'copilot_request_id': msg.id,
            **extra_context
        }
        
        # Collect full response
        response_parts = []
        thinking_parts = []
        
        for event in sc.stream_response(message, context):
            if event.type == 'text':
                response_parts.append(event.content)
            elif event.type == 'thinking':
                thinking_parts.append(event.content)
        
        full_response = ''.join(response_parts)
        
        # Note: streaming_conversation already posts to channel via _post_to_copilot
        # so we don't need to post again here
        
        return jsonify({
            "response": full_response,
            "message_id": msg.id,
            "thinking": thinking_parts if thinking_parts else None
        })
        
    except Exception as e:
        logger.error(f"Error in copilot chat: {e}")
        return jsonify({"error": str(e)}), 500

@copilot_bp.route('/user-chat', methods=['POST'])
def user_chat():
    """
    Send a message to Abby as the human user.
    This allows three-way conversations in the bridge.
    
    Request body:
        - message: The message from the user
    
    Returns:
        - response: Abby's response
        - message_id: ID of the user's message
    """
    try:
        from api_server import get_streaming_conversation_instance
        
        bridge = get_copilot_bridge()
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "message required"}), 400
        
        message = data['message']
        
        # Post user message to channel
        msg = bridge.post_from_user(message, "message")
        
        # Get streaming conversation and process
        sc = get_streaming_conversation_instance()
        if not sc:
            return jsonify({"error": "Abby is not available"}), 503
        
        # Build context
        context = {
            'from_user_bridge': True,
            'user_message_id': msg.id
        }
        
        # Collect full response
        response_parts = []
        
        for event in sc.stream_response(message, context):
            if event.type == 'text':
                response_parts.append(event.content)
        
        full_response = ''.join(response_parts)
        
        # Post Abby's response
        if full_response:
            bridge.post_from_abby(full_response, "response", {
                "in_reply_to": msg.id
            })
        
        return jsonify({
            "response": full_response,
            "message_id": msg.id
        })
        
    except Exception as e:
        logger.error(f"Error in user chat: {e}")
        return jsonify({"error": str(e)}), 500