extends Area2D

@export var rotation_speed: float = 2.0  # 旋转速度（弧度/秒），调整这个值控制快慢。一圈约 2*PI ≈ 6.28

var angle: float = 0.0  # 当前旋转角度

func _ready() -> void:
	add_to_group("letters")  # AudioManager counts these to pace the melody

func _process(delta: float) -> void:
	angle += rotation_speed * delta  # 更新角度，实现连续变化
	$Sprite2D.scale.x = cos(angle)  # 用 cos 模拟 y 轴旋转（scale.x 从 1 到 -1 到 1）

func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		if has_node("/root/GameState"):
			var game_state: GameState = get_node("/root/GameState")
			game_state.collect_letter_bonus()
			queue_free()
