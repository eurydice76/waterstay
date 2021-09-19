class ProgressBar:
    """This class implements a progress bar for the whole application.
    """

    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance

    def __init__(self):

        self._progress_widget = None

    def set_progress_widget(self, progress_widget):

        self._progress_widget = progress_widget

    def reset(self, n_steps):
        """Initializes the progress bar.

        Args:
            n_steps (int): the total number of steps of the task to monitor
        """

        if not self._progress_widget:
            return

        try:
            self._progress_widget.setMinimum(0)
            self._progress_widget.setMaximum(n_steps)
        except AttributeError:
            return

    def update(self, step):
        """Updates the progress bar.

        Args:
            step (int): the step
        """

        if not self._progress_widget:
            return

        try:
            self._progress_widget.setValue(step)
        except AttributeError:
            return


progress_bar = ProgressBar()
