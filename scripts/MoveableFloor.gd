extends StaticBody2D

var player_on_platform = null # 存储站在平台上的玩家引用
var previous_position = Vector2.ZERO # 记录平台上一帧的位置

func _ready():
	_set_tween()
	
func _set_tween():
	# 获取起止点节点（确保在编辑器中已设置）
	var start_point = $StartPoint
	var end_point = $EndPoint
	
	var start_pos: Vector2 = to_global(start_point.position)
	var end_pos: Vector2 = to_global(end_point.position)
	
	# 创建 Tween
	var tween: Tween = get_tree().create_tween()
	tween.tween_property(self, "position", end_pos, 2.0).set_trans(Tween.TRANS_LINEAR).set_ease(Tween.EASE_IN_OUT)
	
	# 可选：循环移动（从起点到终点，再回到起点）
	tween.tween_property(self, "position", start_pos, 2.0)
	tween.set_loops()  # 无限循环

func _physics_process(delta):
	if player_on_platform:
		# 计算平台的移动距离（包括水平和竖直方向）
		var movement = global_position - previous_position
		# 将平台的移动距离应用到玩家的位置
		player_on_platform.global_position += movement
		# 确保玩家的物理行为正常（调用 move_and_slide 处理玩家的 velocity）
		player_on_platform.move_and_slide()
	
	# 更新上一帧的位置
	previous_position = global_position

# 当玩家进入 Area2D 时
func _on_area_2d_body_entered(body):
	if body.has_method("is_player"):
		player_on_platform = body

# 当玩家离开 Area2D 时
func _on_area_2d_body_exited(body):
	if body == player_on_platform:
		player_on_platform = null
