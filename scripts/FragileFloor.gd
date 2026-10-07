extends Area2D


func _on_body_entered(body: Node2D) -> void:
	if body.has_method("is_player"):
		if visible and $DisappearTimer.is_stopped():
			AudioManager.play_sfx("fragile_crack")
		$DisappearTimer.start()
	
func _on_disappear_timer_timeout() -> void:
	visible = false
	AudioManager.play_sfx_at("fragile_break", global_position)
	set_process(false)
	set_physics_process(false)
	get_node("StaticBody2D/CollisionShape2D").set_deferred("disabled", true)
	$AppearTimer.start()

func _on_appear_timer_timeout() -> void:
	$AppearTimer.stop()  # the timer is not one-shot; restore only once
	visible = true
	AudioManager.play_sfx_at("fragile_restore", global_position)
	set_process(true)
	set_physics_process(true)
	get_node("StaticBody2D/CollisionShape2D").set_deferred("disabled", false)
