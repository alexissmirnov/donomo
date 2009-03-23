from django.conf            import settings
from donomo.archive.utils   import sqs
from boto.ec2               import connection
import sys

"""
Prints the number of running instances OR the number of messages in the queue
depending on the input paramater (instances or pending)
"""

def num_instances():
    """ Calculate the number of active (booting or running) instances
    """
    count = 0

    ec2_conn = connection.EC2Connection(
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY )

    for reservation in ec2_conn.get_all_instances():
        for instance in reservation.instances:
            if instance.state in ( 'pending', 'running' ):
                count += 1

    return count

def queue_length():
    """ Calculate the number of work items currently pending in the queue
    """
    return sqs._get_queue().count()

STAT_FUNC = {
    'pending'   : queue_length,
    'instances' : num_instances
}


def main():
    stat_func = STAT_FUNC.get(sys.argv[1], lambda: '#invalid#')
    value     = stat_func()
    print value

if __name__ == '__main__':
    main()
