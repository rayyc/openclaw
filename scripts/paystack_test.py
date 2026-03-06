import os
import asyncio
import json

PAYSTACK_KEY = os.environ.get('PAYSTACK_SECRET_KEY')

if not PAYSTACK_KEY:
    print('SKIPPING_PAYSTACK_TEST: PAYSTACK_SECRET_KEY not set in environment')
    raise SystemExit(0)

os.environ['PAYSTACK_SECRET_KEY'] = PAYSTACK_KEY

from backend.services import paystack_service as ps


async def run_test():
    ref = ps.generate_reference('test-user', 'starter')
    try:
        resp = await ps.initialize_transaction(
            amount=1.0,
            currency='NGN',
            email='test@example.com',
            reference=ref,
            callback_url='http://localhost:8000/billing/webhook',
            metadata={'user_id': 'test-user', 'tier': 'starter'},
        )
        print('PAYSTACK_INIT_RESPONSE:', json.dumps(resp, indent=2))
    except Exception as e:
        print('PAYSTACK_INIT_ERROR:', e)


if __name__ == '__main__':
    asyncio.run(run_test())
