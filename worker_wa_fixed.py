#!/usr/bin/env python3
"""
Camunda 8 WhatsApp Job Worker - pyzeebe 4.7.0 Compatible (Fixed)
================================================================

Worker untuk menangani job 'kirim-notifikasi-wa' menggunakan pyzeebe 4.7.0
dengan pola yang lebih stabil.

Usage:
    source venv/bin/activate
    python worker_wa_fixed.py
"""

import asyncio
import logging
import random
from datetime import datetime
from typing import Dict, Any
from pyzeebe import ZeebeWorker, create_insecure_channel

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("whatsapp-worker")

def process_whatsapp_notification(
    phone_number: str,
    message: str, 
    customer_name: str = "Customer",
    order_id: str = "",
    **kwargs: Any
) -> Dict[str, Any]:
    """
    Handler untuk job WhatsApp notification.
    
    Parameters:
    - phone_number: Nomor HP target (required)
    - message: Template pesan (required) 
    - customer_name: Nama customer (optional)
    - order_id: ID pesanan (optional)
    
    Returns:
    - Dictionary dengan hasil pengiriman
    """
    
    logger.info(f"📱 Processing WhatsApp job for: {phone_number}")
    
    # Validasi input
    if not phone_number or not message:
        error_msg = "Missing required variables: phone_number or message"
        logger.error(f"❌ {error_msg}")
        return {
            "status": "failed",
            "error": error_msg,
            "failed_at": datetime.now().isoformat()
        }
    
    # Format message dengan variabel
    try:
        formatted_message = message.format(
            customer_name=customer_name,
            order_id=order_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    except Exception as e:
        # Jika formatting gagal, gunakan message original
        formatted_message = message
        logger.warning(f"⚠️ Message formatting failed: {e}")
    
    logger.info(f"💬 Message: {formatted_message}")
    
    # Simulasi API WhatsApp (TODO: ganti dengan real API)
    success = random.random() > 0.15  # 85% success rate
    
    if success:
        delivery_id = f"wa_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        result = {
            "status": "success",
            "sent_at": datetime.now().isoformat(),
            "phone_number": phone_number,
            "message_delivered": True,
            "delivery_id": delivery_id,
            "message_content": formatted_message
        }
        logger.info(f"✅ WhatsApp sent successfully - ID: {delivery_id}")
        return result
    else:
        error_reasons = [
            "Network timeout",
            "Invalid phone number", 
            "WhatsApp service unavailable",
            "Rate limit exceeded"
        ]
        error_reason = random.choice(error_reasons)
        
        result = {
            "status": "failed",
            "error": f"Delivery failed - {error_reason}",
            "failed_at": datetime.now().isoformat(),
            "phone_number": phone_number,
            "retry_recommended": True
        }
        logger.error(f"❌ WhatsApp delivery failed: {error_reason}")
        return result


async def run_worker():
    """Run worker dengan connection yang stabil"""
    
    print("Camunda 8 WhatsApp Worker - pyzeebe 4.7.0 (Fixed)")
    print("==================================================")
    print("🚀 Starting WhatsApp notification worker...")
    print("🔧 Zeebe Gateway: localhost:26500")
    print("🏷️ Job Type: kirim-notifikasi-wa")
    print()
    
    try:
        # Create channel and worker
        channel = create_insecure_channel("localhost:26500")
        worker = ZeebeWorker(channel)
        
        # Register task handler
        @worker.task(task_type="kirim-notifikasi-wa")
        def handle_whatsapp_job(
            phone_number: str,
            message: str,
            customer_name: str = "Customer", 
            order_id: str = "",
            **kwargs
        ) -> Dict[str, Any]:
            return process_whatsapp_notification(
                phone_number=phone_number,
                message=message,
                customer_name=customer_name,
                order_id=order_id,
                **kwargs
            )
        
        logger.info("✅ Worker initialized successfully")
        logger.info("⏳ Waiting for jobs... Press Ctrl+C to stop")
        
        # Start worker
        await worker.work()
        
    except KeyboardInterrupt:
        logger.info("👋 Worker stopped by user")
    except Exception as e:
        logger.error(f"❌ Worker error: {e}")
        raise


def test_worker_locally():
    """Test worker function secara lokal tanpa Zeebe"""
    
    print("🧪 Testing WhatsApp worker locally...")
    print("=" * 40)
    
    # Test case 1: Success case
    test_variables = {
        "phone_number": "08123456789",
        "message": "Halo {customer_name}, pesanan {order_id} Anda telah dikonfirmasi pada {timestamp}",
        "customer_name": "John Doe",
        "order_id": "ORD-12345"
    }
    
    print("📝 Test Case 1: Normal message")
    result = process_whatsapp_notification(**test_variables)
    print(f"📊 Result: {result}")
    print()
    
    # Test case 2: Missing phone number
    test_variables_invalid = {
        "phone_number": "",  # Empty phone number
        "message": "Test message",
        "customer_name": "Jane Doe"
    }
    
    print("📝 Test Case 2: Missing phone number")
    result = process_whatsapp_notification(**test_variables_invalid)
    print(f"📊 Result: {result}")
    print()
    
    print("✅ Local testing completed")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run local test
        test_worker_locally()
    else:
        try:
            # Use asyncio to run the main function
            asyncio.run(run_worker())
        except KeyboardInterrupt:
            print("\n👋 Worker stopped")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            
            # Help message
            print("\n" + "="*50)
            print("💡 Troubleshooting:")
            print("1. Make sure Zeebe is running on localhost:26500")
            print("2. Deploy a BPMN process with job type 'kirim-notifikasi-wa'")
            print("3. Start a process instance to generate jobs")
            print("4. Or run local test: python worker_wa_fixed.py --test")
            print("="*50)