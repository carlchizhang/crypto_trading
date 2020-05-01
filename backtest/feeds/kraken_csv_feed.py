from backtrader.feeds import GenericCSVData

class KrakenCSVData(GenericCSVData):
    
    params = (
        ('dtformat', 2),

        ('openinterest', -1),
    )