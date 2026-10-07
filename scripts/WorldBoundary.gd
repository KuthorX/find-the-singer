extends Area2D

func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		if has_node("/root/GameState"):
			var game_state: GameState = get_node("/root/GameState")
			AudioManager.play_sfx("hurt")
			game_state.take_damage(1)
			if game_state.current_health > 0:
				AudioManager.play_sfx_later("respawn", 0.25)
		if body.has_method("move_to_checkpoint"):
			body.move_to_checkpoint()
		
	
