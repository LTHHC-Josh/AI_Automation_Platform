class Task:

    def __init__(
        self,
        row_id,
        name,
        status="",
        assigned_to="",
        percent_complete="",
        latest_comment=""
    ):
        self.row_id = row_id
        self.name = name
        self.status = status
        self.assigned_to = assigned_to
        self.percent_complete = percent_complete
        self.latest_comment = latest_comment

    def __str__(self):
        return self.name