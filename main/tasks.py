from huey.contrib.djhuey import task

@task()
def count_beans(number):
    print('-- counted %s beans --' % number)
    return 'Counted %s beans' % number