from app.domain.fleet.coordinates import (
     format_coordinate,
     is_inside_board,
     parse_coordinate,
)

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

def get_available_coordinates(
          outgoing_shots: list[dict],
) -> list[str]:
     used_coordinates = {
          shot["coordinate"]
          for shot in outgoing_shots
     }

     available_coordinates = []

     for column in "ABCDEFGHIJ":
          for row in range(1, 11):
               coordinate = f"{column}{row}"

               if coordinate not in used_coordinates:
                    available_coordinates.append(coordinate)

     return available_coordinates

def get_neighbor_coordinates(coordinate: str) -> list[str]:
     x, y = parse_coordinate(coordinate)

     neighbor_positions = [
          (x - 1, y),
          (x + 1, y),
          (x, y - 1),
          (x, y + 1),
     ]

     return [
          format_coordinate(position)
          for position in neighbor_positions
          if is_inside_board(position)
     ]

def get_target_coordinates(
          outgoing_shots: list[dict],
) -> list[str]:
     used_coordinates = {
          shot["coordinate"]
          for shot in outgoing_shots
     }

     active_hits = []

     for shot in reversed(outgoing_shots):
          if shot["result"] == "killed":
               break

          if shot["result"] == "hit":
               active_hits.append(shot["coordinate"])

     if not active_hits:
          return []

     if len(active_hits) == 1:
          neighbors = get_neighbor_coordinates(active_hits[0])

          return [
               coordinate
               for coordinate in neighbors
               if coordinate not in used_coordinates
          ]

     positions = [
          parse_coordinate(coordinate)
          for coordinate in active_hits
     ]

     x_values = [x for x, _ in positions]
     y_values = [y for _, y in positions]

     candidate_positions = []

     if len(set(x_values)) == 1:
          x = x_values[0]

          candidate_positions = [
               (x, min(y_values) - 1),
               (x, max(y_values) + 1),
          ]

     elif len(set(y_values)) == 1:
          y = y_values[0]

          candidate_positions = [
               (min(x_values) - 1, y),
               (max(x_values) + 1, y),
          ]

     return [
          format_coordinate(position)
          for position in candidate_positions
          if (
               is_inside_board(position)
               and format_coordinate(position) not in used_coordinates
          )
     ]

def choose_shot_coordinate(
          outgoing_shots: list[dict],
) -> str | None:
     target_coordinates = get_target_coordinates(outgoing_shots)

     if target_coordinates:
          return target_coordinates[0]

     available_coordinates = get_available_coordinates(outgoing_shots)

     if available_coordinates:
          return available_coordinates[0]

     return None