from fastapi import APIRouter

auth_router = APIRouter(prefix="/auth")


@auth_router.post("/register")
async def register_user():
    pass


@auth_router.post("/login")
async def login_user():
    pass


@auth_router.get("/logout")
async def logout_user():
    pass


@auth_router.get("/me")
async def get_current_user():
    pass


@auth_router.delete("/delete-account")
async def delete_user_account():
    pass


@auth_router.put("/edit-account")
async def edit_user_account():
    pass
