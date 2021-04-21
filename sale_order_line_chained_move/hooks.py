# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def _fill_in_related_sale_line(cr):
    """ Update related_sale_line_id on recursive moves

    """
    query = """
        WITH RECURSIVE moves(line_id, move_dest_id, move_orig_id) AS (
            SELECT sm.sale_line_id, smmr.move_orig_id, smmr.move_dest_id
            FROM stock_move_move_rel smmr
            JOIN stock_move sm ON sm.id = smmr.move_dest_id
        UNION ALL
            SELECT sm.sale_line_id, m.move_orig_id, m.move_dest_id
            FROM stock_move sm
            JOIN moves m ON m.move_dest_id = sm.id
            WHERE sm.sale_line_id IS NOT NULL
        ),
        lines (line_id, move_dest_id, move_orig_id) AS (

            SELECT line_id, move_dest_id, move_orig_id
            FROM moves
            UNION
                SELECT moves.line_id, l.move_dest_id, l.move_orig_id
                FROM lines l
                JOIN moves ON moves.move_dest_id = l.move_orig_id
        )
        UPDATE stock_move
            SET related_sale_line_id = (
                SELECT DISTINCT(line_id) FROM lines
                WHERE (stock_move.id IN (move_orig_id, move_dest_id))
                AND line_id IS NOT NULL
            )
            WHERE related_sale_line_id IS NULL AND sale_line_id IS NULL
            AND EXISTS (
                SELECT 1 FROM lines
                WHERE line_id IS NOT NULL
                AND stock_move.id IN (lines.move_orig_id, lines.move_dest_id))
        """
    cr.execute(query)


def post_init_hook(cr, registry):
    _fill_in_related_sale_line(cr)
