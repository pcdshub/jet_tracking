'''
Methods used for testing cam_util methods
'''
from .. import devices
from .. import cam_utils
from .. import move_motor

from time import sleep


def test_get_camroll_pxsize():
    port_names = {'ROI_port': 'ROI1',
                  'ROI_stats_port': 'Stats1',
                  'ROI_image_port': 'IMAGE1'}
    SC1_questar = devices.Questar(**port_names,
                                  prefix='CXI:SC1:INLINE',
                                  name='SC1_questar')

    motor_names = {'name': 'PI1_injector',
                   'coarseX': 'CXI:PI1:MMS:01',
                   'coarseY': 'CXI:PI1:MMS:02',
                   'coarseZ': 'CXI:PI1:MMS:03',
                   'fineX': ' CXI:USR:MMS:01',
                   'fineY': 'CXI:USR:MMS:02',
                   'fineZ': 'CXI:USR:MMS:03'}
    injector_PI1 = devices.Injector(**motor_names)

    # reset motor position
    injector_PI1.coarseX.put(0)
    sleep(3)

    imgs = []
    positions = []

    for i in range(5):
        # get motor positions & images
        imgs.append(SC1_questar.image.image)
        positions.append(injector_PI1.coarseX.get())

        # move motor
        move_motor.movex(injector_PI1.coarseX, -0.1)
        sleep(3)

    # reset motor position
    injector_PI1.coarseX.put(0)
    sleep(3)

    # use motor positions & images to calculate camroll & pxsize
    return cam_utils.get_cam_roll_pxsize(imgs, positions), imgs


def test_get_nozzle_shift():
    camroll_pxsize, imgs = test_get_camroll_pxsize()
    params = {'cam_roll': camroll_pxsize[0], 'pxsize': camroll_pxsize[1]}
    im1 = imgs[0]
    im2 = imgs[4]

    return cam_utils.get_nozzle_shift(im1, im2, params)


def test_jet_detect():
    port_names = {'ROI_port': 'ROI1',
                  'ROI_stats_port': 'Stats1',
                  'ROI_image_port': 'IMAGE1'}
    SC1_questar = devices.Questar(**port_names,
                                  prefix='CXI:SC1:INLINE',
                                  name='SC1_questar')

    return cam_utils.jet_detect(SC1_questar.image.image)


def test_get_cam_coords():
    camroll_pxsize, imgs = test_get_camroll_pxsize()
    '''
    NEED BEAM_X, BEAM_Y
    params = {'cam_roll': camroll_pxsize[0], 'pxsize': camroll_pxsize[1]}
    return cam_utils.get_cam_coords(beam_y, beam_x, params)'''
    return 0


def test_get_jet_x():
    port_names = {'ROI_port': 'ROI1',
                  'ROI_stats_port': 'Stats1',
                  'ROI_image_port': 'IMAGE1'}
    SC1_questar = devices.Questar(**port_names,
                                  prefix='CXI:SC1:INLINE',
                                  name='SC1_questar')
    rho, theta = cam_utils.jet_detect(SC1_questar.image.image)

    camroll_pxsize, imgs = test_get_camroll_pxsize()
    cam_y, cam_x = test_get_cam_coords()

    '''
    params = {'cam_roll': camroll_pxsize[0],
              'pxsize': camroll_pxsize[1],
              'cam_x': cam_x,
              'cam_y': cam_y}
    NEED BEAM_X, BEAM_Y
    return cam_utils.get_jet_x(rho, theta,
                               SC1_questar.ROI,
                               SC1_questar.ROI,
                               params)
    '''
    return 0


def test_get_jet_roll():
    camroll_pxsize, imgs = test_get_camroll_pxsize()
    params = {'cam_roll': camroll_pxsize[0]}

    port_names = {'ROI_port': 'ROI1',
                  'ROI_stats_port': 'Stats1',
                  'ROI_image_port': 'IMAGE1'}
    SC1_questar = devices.Questar(**port_names,
                                  prefix='CXI:SC1:INLINE',
                                  name='SC1_questar')
    rho, theta = cam_utils.jet_detect(SC1_questar.image.image)

    return cam_utils.get_jet_roll(theta, params)


def test_get_jet_width():
    port_names = {'ROI_port': 'ROI1',
                  'ROI_stats_port': 'Stats1',
                  'ROI_image_port': 'IMAGE1'}
    SC1_questar = devices.Questar(**port_names,
                                  prefix='CXI:SC1:INLINE',
                                  name='SC1_questar')
    rho, theta = cam_utils.jet_detect(SC1_questar.image.image)

    return cam_utils.get_jet_width(SC1_questar.image.image,
                                   rho, theta)
