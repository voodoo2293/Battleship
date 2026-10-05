import httpx


class ArenaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def create_game(self) -> dict:
        response = httpx.post(
            f"{self.base_url}/game"
        )

        response.raise_for_status()

        return response.json()

    def close_game(self, session_id: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/game/{session_id}/close"
        )

        response.raise_for_status()

        return response.json()

    def make_shot(self, session_id: str) -> dict:
        response = httpx.post(
            f"{self.base_url}/game/{session_id}/shot"
        )

        response.raise_for_status()

        return response.json()

    def send_opponent_shot(
            self,
            session_id: str,
            coordinate: str,
    ) -> dict:
        response = httpx.post(
            f"{self.base_url}/game/{session_id}/opponent-shot",
            json={"coordinate": coordinate},
        )

        response.raise_for_status()

        return response.json()

    def send_shot_result(
            self,
            session_id: str,
            result: str,
    ) -> dict:
        response = httpx.post(
            f"{self.base_url}/game/{session_id}/shot/result",
            json={"result": result},
        )

        response.raise_for_status()

        return response.json()
    