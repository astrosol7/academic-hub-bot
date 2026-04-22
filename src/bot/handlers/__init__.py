from aiogram import Dispatcher, Router

from .common import HandlerDeps
from .identity import setup_identity
from .navigation import setup_navigation
from .search import setup_search
from .qa import setup_qa
from .ai import setup_ai
from .router_main import setup_fast_router

def register_handlers(
    dispatcher: Dispatcher,
    repository: "PostgresContentRepository",
    navigation: "NavigationService",
    delivery: "DeliveryService",
    search: "SearchService",
    renderer: "TelegramRenderer",
    coordinator: "DeliveryCoordinator",
) -> None:
    router = Router()
    deps = HandlerDeps(
        repository=repository,
        navigation=navigation,
        delivery=delivery,
        search=search,
        renderer=renderer,
        coordinator=coordinator
    )
    
    # AI must be setup before Search (so _offer_ai_help is attached to deps)
    setup_ai(router, deps)
    
    # Navigation provides deps.handle_delivery, deps.find_category_slug
    setup_navigation(router, deps)
    
    # Search uses deps._offer_ai_help and sets up deps.handle_search_mode
    setup_search(router, deps)
    
    # Identity provides /start, /menu, /help, /stop
    setup_identity(router, deps)
    
    # QA provides /ask, /top, /my, /answer and inline buttons
    setup_qa(router, deps)
    
    # Fast router is the fallback text message handler, so setup last
    setup_fast_router(router, deps)

    dispatcher.include_router(router)
