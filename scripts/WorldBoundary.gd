extends Area2D

func _on_body_entered(body: Node2D) -> void:
	print("in")
	if body.has_method("is_player"):
		if has_node("/root/GameState"):
			var game_state: GameState = get_node("/root/GameState")
			game_state.take_damage(1)
		if body.has_method("move_to_checkpoint"):
			body.move_to_checkpoint()
		
	
