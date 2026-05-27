from handlers import (commands, leaderboard,
                      profile, change_lang,
                      verify, tests,
                      resources)

routers_list = [
    commands.router,
    tests.router,
    leaderboard.router,
    profile.router,
    change_lang.router,
    verify.router,
    resources.router,
]
