extends Area2D

# 弹跳的 Y 轴范围（相对于初始位置）
@export var bounce_range: float = 100.0  # 弹跳范围（上下各一半）
@export var speed: float = 2.0           # 弹跳周期速度（控制一个周期的时间）

# 存储初始 Y 位置
var initial_y: float
# 计算出的最小和最大 Y 位置
var min_y: float
var max_y: float
# 时间计数器
var time: float = 0.0

func _ready():
	# 记录初始 Y 位置并计算弹跳范围
	initial_y = position.y
	min_y = initial_y - bounce_range / 2.0
	max_y = initial_y + bounce_range / 2.0

func _process(delta):
	# 累加时间
	time += delta * speed
	# 使用正弦函数计算平滑的 Y 位置
	var t = sin(time)  # sin 返回 -1 到 1 的值
	# 将正弦值映射到 min_y 和 max_y 范围
	position.y = lerp(min_y, max_y, (t + 1.0) / 2.0)  # 将 -1~1 映射到 0~1

func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		if body.has_method("save_checkpoint"):
			body.save_checkpoint(global_position)
			queue_free()
