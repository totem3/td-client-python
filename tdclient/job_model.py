#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals

import time
import warnings

from tdclient.model import Model

class Schema(object):
    """Schema of a database table on Treasure Data Service
    """

    class Field(object):
        def __init__(self, name, type):
            self._name = name
            self._type = type

        @property
        def name(self):
            """
            TODO: add docstring
            """
            return self._name

        @property
        def type(self):
            """
            TODO: add docstring
            """
            return self._type

    def __init__(self, fields=None):
        fields = [] if fields is None else fields
        self._fields = fields

    @property
    def fields(self):
        """
        TODO: add docstring
        """
        return self._fields

    def add_field(self, name, type):
        """
        TODO: add docstring
        """
        self._fields.append(Schema.Field(name, type))

class Job(Model):
    """Job on Treasure Data Service
    """

    STATUS_QUEUED = "queued"
    STATUS_BOOTING = "booting"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_KILLED = "killed"
    FINISHED_STATUS = [STATUS_SUCCESS, STATUS_ERROR, STATUS_KILLED]

    JOB_PRIORITY = {
        -2: "VERY LOW",
        -1: "LOW",
        0: "NORMAL",
        1: "HIGH",
        2: "VERY HIGH",
    }

    def __init__(self, client, job_id, type, query, **kwargs):
        super(Job, self).__init__(client)
        self._job_id = job_id
        self._type = type
        self._query = query
        self._feed(kwargs)

    def _feed(self, data=None):
        data = {} if data is None else data
        self._url = data.get("url")
        self._status = data.get("status")
        self._debug = data.get("debug")
        self._start_at = data.get("start_at")
        self._end_at = data.get("end_at")
        self._cpu_time = data.get("cpu_time")
        self._result = data.get("result")
        self._result_size = data.get("result_size")
        self._result_url = data.get("result_url")
        self._hive_result_schema = data.get("hive_result_schema")
        self._priority = data.get("priority")
        self._retry_limit = data.get("retry_limit")
        self._org_name = data.get("org_name")
        self._db_name = data.get("db_name")
        self._records = data.get("records")

    def update(self):
        """Update all fields of the job
        """
        data = self._client.api.show_job(self._job_id)
        self._feed(data)

    def _update_status(self):
        warnings.warn("_update_status() will be removed from future release. Please use update() instaed.)", category=DeprecationWarning)
        self.update()

    def _update_progress(self):
        """Update `_status` field of the job if it's not finished
        """
        if self._status not in self.FINISHED_STATUS:
            self._status = self._client.job_status(self._job_id)

    @property
    def id(self):
        """
        Returns: a string represents the identifier of the job
        """
        return self._job_id

    @property
    def job_id(self):
        """
        Returns: a string represents the identifier of the job
        """
        return self._job_id

    @property
    def type(self):
        """
        Returns: a string represents the engine type of the job (e.g. "hive", "presto", etc.)
        """
        return self._type

    @property
    def result_size(self):
        """
        Returns: the length of job result
        """
        return self._result_size

    @property
    def result_url(self):
        """
        Returns: a string of URL of the result on Treasure Data Service
        """
        return self._result_url

    @property
    def result_schema(self):
        """
        Returns: an array of array represents the type of result columns (Hive specific) (e.g. [["_c1", "string"], ["_c2", "bigint"]])
        """
        return self._hive_result_schema

    @property
    def priority(self):
        """
        Returns: a string represents the priority of the job (e.g. "NORMAL", "HIGH", etc.)
        """
        if self._priority in self.JOB_PRIORITY:
            return self.JOB_PRIORITY[self._priority]
        else:
            # just convert the value in string
            return str(self._priority)

    @property
    def retry_limit(self):
        """
        TODO: add docstring
        """
        return self._retry_limit

    @property
    def org_name(self):
        """
        Returns: organization name
        """
        return self._org_name

    @property
    def db_name(self):
        """
        Returns: a string represents the name of a database that job is running on
        """
        return self._db_name

    @property
    def debug(self):
        """
        Returns: a :class:`dict` of debug output (e.g. "cmdout", "stderr")
        """
        return self._debug

    def wait(self, timeout=None, wait_interval=5, wait_callback=None, callback=None):
        """Sleep until the job has been finished

        Params:
            timeout (int): Timeout in seconds. No timeout by default.
            wait_interval (int): wait interval in second. Default 5 seconds.
            wait_callback (callable): A callable to be called on every tick of wait interval.
        """
        started_at = time.time()
        while not self.finished():
            if timeout is None or abs(time.time() - started_at) < timeout:
                time.sleep(wait_interval)
                cb = wait_callback if callable(wait_callback) else callback
                if callable(cb):
                    cb(self)
            else:
                raise RuntimeError("timeout") # TODO: throw proper error
        self.update()

    def kill(self):
        """Kill the job

        Returns: a string represents the status of killed job ("queued", "running")
        """
        response = self._client.kill(self.job_id)
        self.update()
        return response

    @property
    def records(self):
        """
        Returns: a number representing the # of records fetched by the query
        """
        return self._records

    @property
    def query(self):
        """
        Returns: a string represents the query string of the job
        """
        return self._query

    def status(self):
        """
        Returns: a string represents the status of the job ("success", "error", "killed", "queued", "running")
        """
        if self._query is not None and not self.finished():
            self.update()
        return self._status

    @property
    def url(self):
        """
        Returns: a string of URL of the job on Treasure Data Service
        """
        return self._url

    def result(self):
        """
        Returns: an iterator of rows in result set
        """
        if not self.success():
            raise ValueError("result is not ready")
        else:
            self.update()
            if self._result is None:
                for row in self._client.job_result_each(self._job_id):
                    yield row
            else:
                for row in self._result:
                    yield row

    def result_format(self, fmt):
        """
        Params:
            fmt (str): output format of result set

        Returns: an iterator of rows in result set
        """
        if not self.success():
            raise ValueError("result is not ready")
        else:
            self.update()
            if self._result is None:
                for row in self._client.job_result_format_each(self._job_id, fmt):
                    yield row
            else:
                for row in self._result:
                    yield row

    def finished(self):
        """
        Returns: `True` if the job has been finished in success, error or killed
        """
        self._update_progress()
        return self._status in self.FINISHED_STATUS

    def success(self):
        """
        Returns: `True` if the job has been finished in success
        """
        self._update_progress()
        return self._status == self.STATUS_SUCCESS

    def error(self):
        """
        Returns: `True` if the job has been finished in error
        """
        self._update_progress()
        return self._status == self.STATUS_ERROR

    def killed(self):
        """
        Returns: `True` if the job has been finished in killed
        """
        self._update_progress()
        return self._status == self.STATUS_KILLED

    def queued(self):
        """
        Returns: `True` if the job is queued
        """
        self._update_progress()
        return self._status == self.STATUS_QUEUED

    def running(self):
        """
        Returns: `True` if the job is running
        """
        self._update_progress()
        return self._status == self.STATUS_RUNNING
