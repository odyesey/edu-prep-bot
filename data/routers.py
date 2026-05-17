from handlers import (commands, leaderboard,
                      profile, change_lang,
                      verify, tests,
                      host_test, resources)

routers_list = [
    resources.router,
    commands.router,
    tests.router,
    leaderboard.router,
    profile.router,
    change_lang.router,
    verify.router,
    host_test.router,
]
