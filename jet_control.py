class JetControl:
    '''
    Jet tracking control class using jet_tracking methods
    '''
    def __init__(self, name, 
            injector, camera, params, 
            #camera_offaxis=None, 
            **kwargs):

        self.injector = injector
        self.camera = camera
        self.params = params

    def set_beam(self, beamX, beamY):
        '''
        Set the coordinates for the x-ray beam

        Parameters
        ----------
        beamX_px : int
            x-coordinate of x-ray beam in the camera image in pixels
        beamY_px : int
            y-coordinate of x-ray beam in the camera image in pixels
        '''
        set_beam(beamX, beamY, self.params)

    def calibrate(self):
        '''
        Calibrate the onaxis camera
        '''
        calibrate(self.injector, self.camera, self.params)


    def jet_calculate(self):
        '''
        Track the sample jet and calculate the distance to the x-ray beam
        '''
        jet_calculate(self.camera, self.params)
       
    
    def jet_move(self):
        '''
        Move the sample jet to the x-ray beam
        '''
        jet_move(self.injector, self.camera, self.params)


def get_burst_avg(n, image_plugin):
    '''
    Get the average of n consecutive images from a camera

    Parameters
    ----------
    n : int
        number of consecutive images to be averaged
    image_plugin : ImagePlugin
        camera ImagePlugin from which the images will be taken

    Returns
    -------
    burst_avg : ndarray
        average image
    '''
    import numpy as np

    imageX, imageY = image_plugin.image.shape
    burst_imgs = np.empty((n, imageX, imageY))
    for x in range(n):
        burst_imgs[x] = image_plugin.image
    burst_avg =  burst_imgs.mean(axis=0)

    return burst_avg



def set_beam(beamX_px, beamY_px, params):
    '''
    Set the coordinates for the x-ray beam

    Parameters
    ----------
    beamX_px : int
        x-coordinate of x-ray beam in the camera image in pixels
    beamY_px : int
        y-coordinate of x-ray beam in the camera image in pixels
    params : Parameters
        EPICS PVs used for recording jet tracking data
    '''
    params.beam_x_px.put(beamX_px)
    params.beam_y_px.put(beamY_px)
    return


def calibrate(injector, camera, params):
    '''
    Calibrate the camera 

    Parameters
    ----------
    injector : Injector
        sample injector
    camera : Questar
        camera looking at sample jet and x-rays
    params : Parameters
        EPICS PVs used for recording jet tracking data
    '''
    from time import sleep
    from cxi import cam_utils

    # find jet in camera ROI
    ROI_image = get_burst_avg(20, camera.ROI_image)
    rho, theta = cam_utils.jet_detect(ROI_image)

    # collect images and motor positions to calculate pxsize and cam_roll
    imgs = []
    positions = []
    start_pos = injector.coarseX.get()
    for i in range(2):
        image = get_burst_avg(20, camera.image)
        imgs.append(image)
        positions.append(injector.coarseX.get())
        injector.coarseX.put(injector.coarseX.get() - 0.1)
        sleep(3)
    injector.coarseX.put(start_pos)
    sleep(3)

    cam_roll, pxsize = cam_utils.get_cam_roll_pxsize(imgs, positions)
    params.pxsize.put(pxsize)
    params.cam_roll.put(cam_roll)
    
    beamX_px = params.beam_x_px.get()
    beamY_px = params.beam_y_px.get()
    camX, camY = cam_utils.get_cam_coords(beamX_px, beamY_px, params)
    params.cam_x.put(camX)
    params.cam_y.put(camY)
    
    jet_roll = cam_utils.get_jet_roll(theta, params)
    params.jet_roll.put(jet_roll)

    return


def jet_calculate(camera, params):
    '''
    Track the sample jet and calculate the distance to the x-ray beam

    Parameters
    ----------
    camera : Questar
        camera looking at the sample jet and x-ray beam
    params : Parameters
        EPICS PVs used for recording jet tracking data
    '''
    from cxi import cam_utils
    
    # track jet position
    print('Running...')
    while True:
        try:
            # detect the jet in the camera ROI
            ROI_image = get_burst_avg(20, camera.ROI_image)
            rho, theta = cam_utils.jet_detect(ROI_image)

            # check x-ray beam position
            beamX_px = params.beam_x_px.get()
            beamY_px = params.beam_y_px.get()
            camX, camY = cam_utils.get_cam_coords(beamX_px, beamY_px, params)
            params.cam_x.put(camX)
            params.cam_y.put(camY)

            # find distance from jet to x-rays
            ROIx = camera.ROI.min_xyz.min_x.get()
            ROIy = camera.ROI.min_xyz.min_y.get()
            jetX = cam_utils.get_jet_x(rho, theta,
                                       ROIx, ROIy, params)
            params.jet_x.put(jetX)
        except KeyboardInterrupt:
            print('Stopped.')
            return


def jet_move(injector, camera, params):
    '''
    Move the sample jet to the x-ray beam

    Parameters
    ----------
    injector : Injector
        sample injector
    camera : Questar
        camera looking at the sample jet and x-ray beam
    params : Parameters
        EPICS PVs used for recording jet tracking data
    '''
    from time import sleep
    from cxi.move_motor import movex

    while True:
        try:
            ROIx = camera.ROI.min_xyz.min_x.get()
            ROIy = camera.ROI.min_xyz.min_y.get()

            if abs(params.jet_x.get()) > 0.01:
                # move jet to x-rays using injector motor
                print(f'Moving {params.jet_x.get()} mm')
                movex(injector.coarseX, -params.jet_x.get())
                # move the ROI to keep looking at the jet
                camera.ROI.min_xyz.min_x.put(ROIx + (params.jet_x.get()/params.pxsize.get()))
            # if params.state == [some state]
            #     [use [x] for jet tracking]
            # else if params.state == [some other state]:
            #     [use [y] for jet tracking]
            # else if params.state == [some other state]:
            #     [revert to manual injector controls]
            # etc...            

            # if jet is clear in image:
            #     if jetX != beamX:
            #         move injector.coarseX
            #         walk_to_pixel(detector, motor, target) ??
            # else if nozzle is clear in image:
            #     if nozzleX != beamX:
            #         move injector.coarseX
            # else:
            #     if injector.coarseX.get() != beam_x:
            #         move injector.coarseX
            sleep(5)
        except KeyboardInterrupt:
            return


