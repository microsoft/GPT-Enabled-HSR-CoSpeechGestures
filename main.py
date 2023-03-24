import os
import json
import multiprocessing
import numpy as np
import rospy
from std_srvs.srv import Empty, EmptyRequest
import hsrb_interface
import utils.luis as luis
import utils.aimodels as aimodels
import utils.gestureengine as gestureengine
import utils.speech_synthesizer as speech_synthesizer
from mutagen.mp3 import MP3 as mp3
import pygame

# ------------------------------
laban_dir = "data/LabanotationLibrary"
jsonfiles = os.listdir(laban_dir)
with open('./secrets.json') as f:
    credentials = json.load(f)
# Choose your preferred AImodel
chatmodel = aimodels.ChatGPT  # aimodels.Davinci3
# Choose your preferred gesture selection mode
# gestureengine.luis() # gestureengine.bert() # gestureengine.random()
gestureengine = gestureengine.bert()
# ------------------------------

rospy.init_node('test')
stop_client = rospy.ServiceProxy('/viewpoint_controller/stop', Empty)
stop_client.call(EmptyRequest())
robot = hsrb_interface.Robot()
omni_base = robot.get('omni_base')
whole_body = robot.get('whole_body')
gripper = robot.get('gripper')


def move_to_laban(rospy, item):
    import actionlib
    import rospy
    import control_msgs.msg
    import controller_manager_msgs.srv
    import trajectory_msgs.msg
    import numpy as np
    goal_time = item['time'] / 1000.0
    # print(goal_time)
    radian_arm_flex_joint = 0
    radian_arm_roll_joint = 0
    radian_wrist_flex_joint = 0

    # map lower limb
    laban_lower_limb = item['wrist']
    level_lower_limb = laban_lower_limb.split('-')[1].lower()
    pan_lower_limb = laban_lower_limb.split('-')[0].lower()
    # print(laban_lower_limb)

    if level_lower_limb == 'high':
        radian_arm_flex_joint = 0
    elif level_lower_limb == 'normal':
        radian_arm_flex_joint = np.pi / 12
    elif level_lower_limb == 'low':
        radian_arm_flex_joint = np.pi / 6

    if 'left forward' == pan_lower_limb:
        radian_arm_roll_joint = -1 * np.pi / 12
    elif 'left' == pan_lower_limb:
        radian_arm_roll_joint = -1 * np.pi / 6
    elif 'right forward' == pan_lower_limb:
        radian_arm_roll_joint = np.pi / 12
    elif 'right' == pan_lower_limb:
        radian_arm_roll_joint = np.pi / 6
    else:
        radian_arm_roll_joint = 0

    # initialize action client
    cli_body = actionlib.SimpleActionClient(
        '/hsrb/arm_trajectory_controller/follow_joint_trajectory',
        control_msgs.msg.FollowJointTrajectoryAction)

    # wait for the action server to establish connection
    cli_body.wait_for_server()

    # make sure the controller is running
    rospy.wait_for_service('/hsrb/controller_manager/list_controllers')
    list_controllers = rospy.ServiceProxy(
        '/hsrb/controller_manager/list_controllers',
        controller_manager_msgs.srv.ListControllers)
    running = False
    while running is False:
        rospy.sleep(0.1)
        for c in list_controllers().controller:
            if c.name == 'arm_trajectory_controller' and c.state == 'running':
                running = True

    # fill ROS message
    goal_body = control_msgs.msg.FollowJointTrajectoryGoal()
    traj = trajectory_msgs.msg.JointTrajectory()
    traj.joint_names = [
        "arm_lift_joint",
        "arm_flex_joint",
        "arm_roll_joint",
        "wrist_flex_joint",
        "wrist_roll_joint"]
    p = trajectory_msgs.msg.JointTrajectoryPoint()
    p.positions = [0.0, -
                   1 *
                   radian_arm_flex_joint, -
                   1 *
                   radian_arm_roll_joint, -
                   1.5713076761221076 +
                   radian_arm_flex_joint +
                   radian_wrist_flex_joint, 0.0]
    # print(p.positions)
    p.velocities = [0, 0, 0, 0, 0]
    p.time_from_start = rospy.Duration(goal_time)
    traj.points = [p]
    goal_body.trajectory = traj
    # print('joint')
    # map head
    laban_head = item['head']
    pan_head_joint = 0
    pan_head_joint = 0
    # print(laban_head)
    pan_head = laban_head.split('-')[0].lower()
    tilt_head = laban_head.split('-')[1].lower()
    # print(laban_lower_limb)

    if tilt_head == 'high':
        tilt_head_joint = np.pi / 6  # np.pi/12
    elif tilt_head == 'normal':
        tilt_head_joint = 0
    elif tilt_head == 'low':
        tilt_head_joint = -1 * np.pi / 6  # -np.pi/12

    elif 'left forward' == pan_head:
        pan_head_joint = np.pi / 12
    elif 'left' == pan_head:
        pan_head_joint = np.pi / 6
    elif 'right forward' == pan_head:
        pan_head_joint = -1 * np.pi / 12
    elif 'right' == pan_head:
        pan_head_joint = -1 * np.pi / 6
    else:
        pan_head_joint = 0
    # initialize action client
    cli_head = actionlib.SimpleActionClient(
        '/hsrb/head_trajectory_controller/follow_joint_trajectory',
        control_msgs.msg.FollowJointTrajectoryAction)

    # wait for the action server to establish connection
    cli_head.wait_for_server()

    # make sure the controller is running
    rospy.wait_for_service('/hsrb/controller_manager/list_controllers')
    list_controllers = rospy.ServiceProxy(
        '/hsrb/controller_manager/list_controllers',
        controller_manager_msgs.srv.ListControllers)
    running = False
    while running is False:
        rospy.sleep(0.1)
        for c in list_controllers().controller:
            if c.name == 'head_trajectory_controller' and c.state == 'running':
                running = True
    # fill ROS message
    goal_head = control_msgs.msg.FollowJointTrajectoryGoal()
    traj = trajectory_msgs.msg.JointTrajectory()
    traj.joint_names = ["head_pan_joint", "head_tilt_joint"]
    p = trajectory_msgs.msg.JointTrajectoryPoint()
    p.positions = [pan_head_joint, tilt_head_joint]  # [pan_head, tilt_head]

    p.velocities = [0, 0]
    p.time_from_start = rospy.Duration(goal_time)
    traj.points = [p]
    goal_head.trajectory = traj

    # send message to the action server
    cli_body.send_goal(goal_body)
    cli_head.send_goal(goal_head)

    # wait for the action server to complete the order
    cli_body.wait_for_result()
    cli_head.wait_for_result()
    return True


def move_robot(sequence):
    gripper.command(0.1)
    whole_body.move_to_neutral()
    for item in sequence:
        move_to_laban(rospy, item)
    gripper.command(0.1)
    whole_body.move_to_neutral()


def load_laban(jsondir, jsonfile, time_speech=None):
    with open(os.path.join(jsondir, jsonfile)) as f:
        data = json.load(f)
        data = data[jsonfile.split('.')[0]]
    sequence = []
    current_time = 0
    for item in data:
        try:
            duration = int(data[item]['start time'][0]) - current_time
        except BaseException:
            duration = 1000
            print(item)
        if duration < 0:
            import sys
            sys.stderr.write("Error!")
        sequence.append(
            {
                'elbow': '-'.join(data[item]['left elbow']),
                'wrist': '-'.join(data[item]['left wrist']),
                'head': '-'.join(data[item]['head']),
                'time': duration
            }
        )
        current_time = current_time + duration
    if time_speech is not None:
        if time_speech > current_time:
            ratio = time_speech / float(current_time)
            for i in sequence:
                i['time'] = int(i['time'] * ratio)
    data_save = {}
    data_save[jsonfile.split('.')[0]] = sequence
    # save json file
    with open(os.path.join("generated_files/tmplaban.json"), "w") as f:
        json.dump(data_save, f, indent=4)
    return sequence


def interface(user_input, aimodel):
    # if user_input does not ends with ., ?, or !, add period
    if user_input[-1] not in ['.', '?', '!']:
        user_input = user_input + '.'
    aimodel_message = aimodel.generate(user_input)
    return aimodel_message


def gestureselector(agent_input):
    # any algorithm is OK, as long as it returns intent from user input.
    # intent should be the prefix of the json file (e.g., away, deictic, etc.)
    intent = gestureengine.analyze_input(agent_input)
    print('intent is:' + intent)
    jsoncandidate = []
    for jsonfile in jsonfiles:
        if jsonfile.startswith(intent):
            jsoncandidate.append(jsonfile)

    if len(jsoncandidate) == 0:
        jsoncandidate = jsonfiles
    np.random.shuffle(jsoncandidate)
    # create speech synthesizer every time as it continuously generates audio
    speech_synthesizer_azure_file = speech_synthesizer.speech_synthesizer_file(
        credentials["speech_synthesizer"],
        speech_synthesis_voice_name="en-US-TonyNeural")
    speech_synthesizer_azure_file.synthesize_speech(agent_input)
    del speech_synthesizer_azure_file
    mp3_length = mp3(
        "generated_files/tmpaudio.mp3").info.length
    length_ms = int(mp3_length * 1000)
    print('gesture duration:' + str(length_ms))
    laban = load_laban(laban_dir, jsoncandidate[0], time_speech=length_ms)
    return laban

def play_sound(filename):
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play(1)

if __name__ == "__main__":
    aimodel = chatmodel(credentials)
    luis_handler_intent = luis.luis(credentials)
    status = 'robot_not_talking'
    with multiprocessing.Pool(1) as pool:
        while True:
            user_input = input("input:")
            if user_input == "q":
                break
            if len(user_input) == 0:
                continue
            agent_return = interface(user_input, aimodel)
            if agent_return is not None:
                print('--------------')
                print(agent_return)
                print('--------------')
                laban = gestureselector(agent_return)
                pool.apply_async(play_sound, ("generated_files/tmpaudio.mp3",))
                print('generating motions...')
                move_robot(laban)
                print('done')
            else:
                pass
        robot.close()
