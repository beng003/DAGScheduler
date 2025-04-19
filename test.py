from utils.common_util import SnakeCaseUtil
import json

a = {
    "taskUid": "job-alice-bob-040",
    "taskName": "task2",
    "taskInitiator": "alice",
    "taskGroup": "default",
    "taskYaml": [
        {
            "jobUid": "psi3",
            "jobName": "psi1",
            "jobParties": "[\"party1\",\"party2\"]",
            "jobDependencies": "[]",
            "jobExecutor": "default",
            "invokeTarget": "module_task.scheduler_test.job",
            "jobArgs": "",
            "jobKwargs": ""
        },
        {
            "jobUid": "psi4",
            "jobName": "psi2",
            "jobParties": "[\"party1\",\"party2\"]",
            "jobDependencies": "[\"psi3\"]",
            "jobExecutor": "default",
            "invokeTarget": "module_task.scheduler_test.job",
            "jobArgs": "",
            "jobKwargs": ""
        }
    ],
    "concurrent": "1",
    "cronExpression": "0/10 * * * * ?",
    "misfirePolicy": "3",
    "status": "1",
    "priority": "0",
    "remark": "test"
}

a["taskYaml"] = SnakeCaseUtil.transform_result(a["taskYaml"])
print(json.dumps(SnakeCaseUtil.transform_result(a)))