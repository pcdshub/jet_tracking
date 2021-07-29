

class Ui_MainWindow(object):
    def setupUi(self, obj):
        obj.setMinimumSize(self.minimumSizeHint())
        obj.setObjectName("Simulation Tools")

    def minimumSizeHint(self):
        return (QSize(400, 800))