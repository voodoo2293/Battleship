def get_shot_result(
    ships: list[dict],
    received_shots: list[str],
    coordinate: str,
) -> str:
    target_ship = None

    for ship in ships:
        if coordinate in ship["coordinates"]:
            target_ship = ship["coordinates"]
            break

    if target_ship is None:
            return "miss"
    
    if coordinate in received_shots:
         return "hit"

    shots_after_current = set(received_shots)
    shots_after_current.add(coordinate)

    if all(
         ship_coordinate in shots_after_current
         for ship_coordinate in target_ship
    ):
         return "killed"

    return "hit"