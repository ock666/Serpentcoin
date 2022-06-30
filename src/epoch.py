import requests

class Epoch:
    """
    variables to store the epoch info
    """
    block_epoch = 100
    target_time = 60000
    allowed_variance = 20000

    def epoch_variance(self, epoch_time):
        if epoch_time > Epoch.target_time:
            factor = epoch_time / Epoch.target_time
            return factor

        if epoch_time < Epoch.target_time:
            diff = Epoch.target_time - epoch_time
            factor = diff / Epoch.target_time
            return factor #outputs fx .25


    def epoch_complete(self, chain):
        """
        checks if a difficulty epoch is complete
        returns True if correct, and False if not.
        """
        last_block = chain[-1]
        index = last_block['index']
        print(last_block, index)

        if int(index) % self.block_epoch == 0:
            print("Epoch complete")
            return True
        print("Epoch not complete")
        return False

    def epoch_time(self, epoch_start, epoch_end):
        """
        Subtracts the end time of an epoch from the start time
        returns total Epoch time (time for the network to mine 100 blocks)
        """
        unix_time = epoch_end - epoch_start
        print(f'Epoch Time: {unix_time}')
        return unix_time

    def get_epoch_start(self, chain):
        """
        Get the block time from (current block index - 100)
        returns the beginning time of an epoch
        """
        start_time = self.block_time(chain[-100])
        print(f'Epoch Start: {start_time}')
        return start_time

    def get_epoch_end(self, chain):
        """
        function to get the block time when an epoch has passed.
        returns last_block['timestamp']
        """
        last_block_time = self.block_time(self.last_block(chain))
        print(f'Epoch End: {last_block_time}')
        return last_block_time

    @staticmethod
    def block_time(block):
        """
        Returns the timestamp from a given block in unix millis
        """
        return block['timestamp']

    @staticmethod
    def last_block(chain):
        """
        Returns the last block in the chain
        """
        return chain[-1]

    @staticmethod
    def get_difficulty(node):
        """
        returns the difficulty from a registered node.
        """
        response = requests.get(f'{node}/difficulty')
        return response.json()

    @staticmethod
    def evaluate_epoch_difficulty(chain):
        """
        function to check the time of an epoch and compare it to the actual time of an epoch.
        returns True if the epoch time is greater than the epoch target time + allowed variance
        returns False if the epoch time is less than the epoch time
        returns "difficulty stable" if the epoch time is within the target +- variance.
        """
        try:
            # check if the epoch is finished
            if Epoch.epoch_complete(chain):
                # get the relevant epoch time info if the epoch is complete
                epoch_start = Epoch.get_epoch_start(chain)
                epoch_end = Epoch.get_epoch_end(chain)

                # epoch time is calculated by looking 100 blocks into the past and checking the timestamp.
                # and subtracting that value from the timestamp of the final block within an epoch.
                epoch_time = Epoch.epoch_time(epoch_start=epoch_start, epoch_end=epoch_end)

                # creating variables to store Epoch data
                target_time = Epoch.target_time
                variance = Epoch.allowed_variance

                # if an epoch time is greater than the target time + allowed variance
                # return True to decrease the chain difficulty
                if epoch_time > (target_time + variance):
                    return True

                # if an epoch time is less than the target time - allowed variance
                # return False to reduce chain difficulty
                if epoch_time < (target_time - variance):
                    return False

                return 'difficulty stable'
            return "Epoch not complete"
        except:
            pass
            return "Error occured"


Epoch = Epoch()