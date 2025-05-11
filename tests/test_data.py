task_data = {
    "task_uid": "03414a73-dc74-4b51-a894-75ec47d153d0",
    "task_name": "task2",
    "task_initiator": "alice",
    "task_group": "default",
    "task_yaml": [
        {
            "job_uid": "psi3",
            "job_name": "psi1",
            "job_parties": '["party1","party2"]',
            "job_dependencies": "[]",
            "job_executor": "default",
            "invoke_target": "module_task.scheduler_test.job",
            "job_args": "",
            "job_kwargs": "",
        },
        {
            "job_uid": "psi4",
            "job_name": "psi2",
            "job_parties": '["party1","party2"]',
            "job_dependencies": '["psi3"]',
            "job_executor": "default",
            "invoke_target": "module_task.scheduler_test.job",
            "job_args": "",
            "job_kwargs": "",
        },
    ],
    "create_by": "admin",
    "concurrent": "1",
    "cron_expression": "0/10 * * * * ?",
    "misfire_policy": "3",
    "status": "1",
    "priority": "0",
    "remark": "test",
}

job_list = [{'job_uid': 'psi3', 'job_executor': 'default', 'invoke_target': 'module_task.scheduler_test.job', 'job_args': '', 'job_kwargs': ''}]