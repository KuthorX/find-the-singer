extends Area2D


func _on_body_entered(body: Node2D) -> void:
	if body.has_method("is_player"):
		$DisappearTimer.start()
	
func _on_disappear_timer_timeout() -> void:
	visible = false
	set_process(false)
	set_physics_process(false)
	get_node("StaticBody2D/CollisionShape2D").set_deferred("disabled", true)
	$AppearTimer.start()

func _on_appear_timer_timeout() -> void:
	visible = true
	set_process(true)
	set_physics_process(true)
	get_node("StaticBody2D/CollisionShape2D").set_deferred("disabled", false)
