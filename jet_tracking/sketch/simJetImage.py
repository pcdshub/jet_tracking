import numpy as np
import cv2
from tools.imGen import read_noise, jet_display


class SimulatedImage:
    """SimulatedImage class generates and manages a simulated image.

    Args:
        context (object): The context object containing relevant information.
        signals (object): The signals object for connecting to external signals.

    Attributes:
        context (object): The context object containing relevant information.
        signals (object): The signals object for connecting to external signals.
        jet_im (numpy.ndarray): The simulated image array.
        x_size (int): The width of the simulated image in pixels.
        y_size (int): The height of the simulated image in pixels.
        pix_per_mm (int): The number of pixels per millimeter in the image.
        jet_location (int): The current location of the simulated jet.
        motor_position (int): The current motor position.
    """
    def __init__(self, context, signals):
        """Initialize the SimulatedImage object.

        Args:
            context (object): The context object containing relevant information.
            signals (object): The signals object for connecting to external signals.
        """
        self.context = context
        self.signals = signals
        self.jet_im = []
        self.x_size = 500
        self.y_size = 500
        self.pix_per_mm = 1000
        self.jet_location = 0
        self.motor_position = 0
        self.gen_image()
        self.make_connections()

    def make_connections(self):
        """Make connections to external signals.

        Connects the 'changeReadPosition' signal to the 'update_motor_position' method.
        """
        self.signals.changeReadPosition.connect(
            self.update_motor_position)

    def update_motor_position(self, p):
        """Update the motor position.

        Args:
            p (int): The new motor position.
        """
        self.motor_position = p

    def gen_image(self):
        """Generate the simulated image.

        Creates a simulated image array using the specified parameters and updates the 'jet_im' attribute.
        """
        self.jet_im = np.full((self.y_size, self.x_size), 0, dtype=np.uint8)
        self.jet_im = jet_display(self.jet_im, self.motor_position, self.context.jet_center,
                                  self.pix_per_mm, self.x_size)



