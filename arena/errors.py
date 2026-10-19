from arena.models import ServiceConfig

class InvalidFleetError(Exception):
    def __init__(self, service: ServiceConfig):
        self.service = service

        super().__init__(
            f"{service.name} returned invalid fleet"
        )

class DishonestServiceError(Exception):
    def __init__(
            self,
            service,
            coordinate: str,
            expected: str,
            actual: str,
    ):
        self.service = service
        self.coordinate = coordinate
        self.expected = expected
        self.actual = actual

        super().__init__(
            f"{service.name} returned {actual} for "
            f"{coordinate}, expected {expected}"
        )

class InvalidShotError(Exception):
    def __init__(
            self,
            service,
            coordinate: str,
    ):
        self.service = service
        self.coordinate = coordinate

        super().__init__(
            f"{service.name} returned invalid shot "
            f"coordinate {coordinate}"
        )

class RepeatedShotError(Exception):
    def __init__(
            self,
            service,
            coordinate: str,
    ):
        self.service = service
        self.coordinate = coordinate

        super().__init__(
            f"{service.name} repeated shot "
            f"coordinate {coordinate}"
        )

class ServiceTimeoutError(Exception):
    def __init__(self, service):
        self.service = service

        super().__init__(
            f"{service.name} exceeded request timeout"
        )

class ServiceConnectionError(Exception):
    def __init__(self, service):
        self.service = service

        super().__init__(
            f"{service.name} is unavailable"
        )

class ServiceHTTPError(Exception):
    def __init__(
            self,
            service,
            status_code: int,
    ):
        self.service = service
        self.status_code = status_code

        super().__init__(
            f"{service.name} returned HTTP "
            f"{status_code}"
        )

class ServiceResponseError(Exception):
    def __init__(
            self,
            service,
            message: str,
    ):
        self.service = service

        super().__init__(
            f"{service.name} returned invalid response: "
            f"{message}"
        )