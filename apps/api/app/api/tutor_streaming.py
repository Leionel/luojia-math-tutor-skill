"""Keep disconnect cancellation active even when no model chunk is arriving."""
import asyncio

import anyio
from starlette.responses import StreamingResponse


class TutorStreamingResponse(StreamingResponse):
    async def __call__(self, scope, receive, send):
        # ASGI 2.4 StreamingResponse relies on send() raising after disconnect.
        # A buffered model may never reach send(), so own a receive listener too.
        streaming = asyncio.create_task(self.stream_response(send))
        disconnected = asyncio.create_task(self.listen_for_disconnect(receive))
        try:
            done, _ = await asyncio.wait({streaming,disconnected},return_when=asyncio.FIRST_COMPLETED)
            if streaming in done:
                await streaming
            else:
                await disconnected
        finally:
            # Drain the graph's owned processes and durable writes before the
            # request exits. No detached cancellation/background replay.
            with anyio.CancelScope(shield=True):
                for task in (streaming,disconnected):
                    if not task.done():
                        task.cancel()
                await asyncio.gather(streaming,disconnected,return_exceptions=True)
                close = getattr(self.body_iterator,"aclose",None)
                if close:
                    await close()
        if self.background:
            await self.background()
